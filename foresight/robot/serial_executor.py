from __future__ import annotations

import json

from foresight.config import CONFIG, AppConfig
from foresight.schemas import RobotExecutionResult, RobotSkillRequest, SafetyDecision


class SerialRobotExecutor:
    def __init__(self, config: AppConfig = CONFIG):
        self.config = config

    def execute(self, decision: SafetyDecision, skill: RobotSkillRequest) -> RobotExecutionResult:
        if decision.status != "READY_FOR_EXECUTOR" or not decision.allowed:
            return RobotExecutionResult(sent=False, reason="Blocked by safety gate", executor="serial")
        if not self.config.robot_serial_port:
            return RobotExecutionResult(sent=False, reason="ROBOT_SERIAL_PORT is not configured", executor="serial")
        try:
            import serial  # type: ignore

            with serial.Serial(self.config.robot_serial_port, self.config.robot_serial_baud, timeout=1.0) as ser:
                line = json.dumps(skill.model_dump()).encode("utf-8") + b"\n"
                ser.write(line)
            return RobotExecutionResult(sent=True, reason="Serial JSON line sent", executor="serial")
        except Exception as exc:
            return RobotExecutionResult(sent=False, reason=str(exc), executor="serial")
