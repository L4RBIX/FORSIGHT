"""
DeepSeek Brain — семантический «мозг» робота.

Принимает текстовую команду оператора, возвращает структурированный план:
  - drive  — целевые скорости Husky (линейная / угловая)
  - manipulate — команда для Foresight pipeline (push, point_at, scan, stop)
  - stop   — немедленная остановка

Без DEEPSEEK_API_KEY используется локальный парсер foresight + эвристики.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Literal

import requests

from foresight.parser.command_parser import parse_command
from foresight.schemas import FullPipelineResult, ParsedCommand

ActionMode = Literal["drive", "manipulate", "stop", "scan"]


@dataclass(slots=True)
class BrainPlan:
    mode: ActionMode
    target_linear: float = 0.0
    target_angular: float = 0.0
    duration_sec: float = 0.0
    raw_command: str = ""
    manipulation_text: str = ""
    parsed: ParsedCommand | None = None
    reason: str = ""
    source: str = "local"
    pipeline_result: FullPipelineResult | None = None


# Простые RU/KZ/EN эвристики для навигации Husky (fallback без API)
_DRIVE_PATTERNS: list[tuple[re.Pattern[str], float, float, float]] = [
    (re.compile(r"\b(впер[её]д|forward|ahead|алға|алга)\b", re.I), 1.4, 0.0, 6.0),
    (re.compile(r"\b(назад|back|reverse|артқа|артка)\b", re.I), -0.9, 0.0, 4.0),
    (re.compile(r"\b(влево|left|солға|solga)\b", re.I), 0.4, 0.35, 3.0),
    (re.compile(r"\b(вправо|right|оңға|onga)\b", re.I), 0.4, -0.35, 3.0),
    (re.compile(r"\b(медлен|slow|баяу|bayau|осторож)\b", re.I), 0.6, 0.0, 8.0),
    (re.compile(r"\b(проход|passage|gap|узк)\b", re.I), 0.9, 0.05, 12.0),
    (re.compile(r"\b(стоп|stop|halt|тоқта|tokta)\b", re.I), 0.0, 0.0, 0.0),
]


class DeepSeekBrain:
    """Текст → BrainPlan. DeepSeek API или локальный fallback."""

    def __init__(self) -> None:
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.api_url = os.getenv(
            "DEEPSEEK_API_URL",
            "https://api.deepseek.com/chat/completions",
        )
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout_s = float(os.getenv("DEEPSEEK_TIMEOUT_S", "15"))
        self._warned_no_key = False

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _local_drive_heuristic(self, text: str) -> BrainPlan | None:
        lowered = text.lower()
        for pattern, lin, ang, duration in _DRIVE_PATTERNS:
            if pattern.search(lowered):
                if lin == 0.0 and ang == 0.0:
                    return BrainPlan(
                        mode="stop",
                        raw_command=text,
                        reason="Локальный парсер: стоп",
                        source="local",
                    )
                return BrainPlan(
                    mode="drive",
                    target_linear=lin,
                    target_angular=ang,
                    duration_sec=duration,
                    raw_command=text,
                    reason=f"Локальная эвристика: lin={lin:.2f}, ang={ang:.2f}",
                    source="local",
                )
        return None

    def _local_parse(self, text: str) -> BrainPlan:
        drive = self._local_drive_heuristic(text)
        if drive is not None:
            try:
                drive.parsed = parse_command(text)
            except Exception:
                pass
            return drive

        parsed = parse_command(text)
        if parsed.action == "stop":
            return BrainPlan(
                mode="stop",
                raw_command=text,
                parsed=parsed,
                reason="Локальный парсер: stop",
                source="local",
            )
        if parsed.action == "scan_scene":
            return BrainPlan(
                mode="scan",
                raw_command=text,
                parsed=parsed,
                reason="Локальный парсер: scan_scene",
                source="local",
            )
        return BrainPlan(
            mode="manipulate",
            raw_command=text,
            manipulation_text=text,
            parsed=parsed,
            reason="Локальный парсер → Foresight pipeline",
            source="local",
        )

    def _deepseek_request(self, text: str, context: dict[str, Any]) -> dict[str, Any]:
        system = (
            "You are the semantic brain of a mobile robot (Husky) in a PyBullet simulation. "
            "Return ONLY valid JSON with keys: "
            'mode ("drive"|"manipulate"|"stop"|"scan"), '
            "target_linear (m/s, -1.5..3.0), target_angular (rad/s, -0.55..0.55), "
            "duration_sec (float), manipulation_text (string, original or refined command), "
            "reason (short Russian explanation). "
            "Use mode=drive for navigation through narrow passage. "
            "Use mode=manipulate for push/point_at object tasks. "
            "Use mode=stop for emergency halt."
        )
        user = json.dumps({"operator_command": text, "context": context}, ensure_ascii=False)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    def _plan_from_api_json(self, text: str, data: dict[str, Any]) -> BrainPlan:
        mode = str(data.get("mode", "manipulate")).lower()
        if mode not in ("drive", "manipulate", "stop", "scan"):
            mode = "manipulate"
        return BrainPlan(
            mode=mode,  # type: ignore[arg-type]
            target_linear=float(data.get("target_linear", 0.0)),
            target_angular=float(data.get("target_angular", 0.0)),
            duration_sec=float(data.get("duration_sec", 5.0)),
            raw_command=text,
            manipulation_text=str(data.get("manipulation_text", text)),
            reason=str(data.get("reason", "DeepSeek")),
            source="deepseek",
        )

    def interpret(
        self,
        text: str,
        context: dict[str, Any] | None = None,
    ) -> BrainPlan:
        """Интерпретировать текст оператора в план действий."""
        text = text.strip()
        if not text:
            return BrainPlan(mode="stop", reason="Пустая команда", source="local")

        ctx = context or {}

        if not self.api_key:
            if not self._warned_no_key:
                print(
                    "[BRAIN] DEEPSEEK_API_KEY не задан — локальный парсер + эвристики. "
                    "Добавьте ключ в .env для семантического мозга."
                )
                self._warned_no_key = True
            return self._local_parse(text)

        try:
            data = self._deepseek_request(text, ctx)
            plan = self._plan_from_api_json(text, data)
            print(f"[BRAIN] DeepSeek → {plan.mode}: {plan.reason}")
            return plan
        except Exception as exc:
            print(f"[BRAIN] DeepSeek ошибка ({exc}) — fallback на локальный парсер.")
            return self._local_parse(text)

    def attach_pipeline_result(
        self,
        plan: BrainPlan,
        result: FullPipelineResult,
    ) -> BrainPlan:
        plan.pipeline_result = result
        return plan


@dataclass
class ActiveDriveOverride:
    """Временное перекрытие камеры — команда от мозга."""

    plan: BrainPlan
    expires_at: float = field(default=0.0)

    def is_active(self, now: float) -> bool:
        return self.plan.mode == "drive" and now < self.expires_at

    def velocities(self) -> tuple[float, float]:
        return self.plan.target_linear, self.plan.target_angular
