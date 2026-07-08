from __future__ import annotations

import requests

from foresight.config import CONFIG, AppConfig
from foresight.schemas import RobotExecutionResult, RobotSkillRequest, SafetyDecision


class HttpRobotExecutor:
    def __init__(self, config: AppConfig = CONFIG):
        self.config = config

    def execute(self, decision: SafetyDecision, skill: RobotSkillRequest) -> RobotExecutionResult:
        if decision.status != "READY_FOR_EXECUTOR" or not decision.allowed:
            return RobotExecutionResult(sent=False, reason="Blocked by safety gate", executor="http")
        payload = skill.model_dump()
        try:
            response = requests.post(self.config.robot_http_url, json=payload, timeout=self.config.robot_http_timeout_s)
            return RobotExecutionResult(sent=response.ok, reason=f"HTTP status {response.status_code}", executor="http", response=response.text[:500])
        except Exception as exc:
            return RobotExecutionResult(sent=False, reason=str(exc), executor="http")
