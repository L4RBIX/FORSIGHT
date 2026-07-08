from __future__ import annotations

from typing import Protocol

from foresight.schemas import RobotExecutionResult, RobotSkillRequest, SafetyDecision


class RobotExecutor(Protocol):
    def execute(self, decision: SafetyDecision, skill: RobotSkillRequest) -> RobotExecutionResult:
        ...


class DryRunExecutor:
    def execute(self, decision: SafetyDecision, skill: RobotSkillRequest) -> RobotExecutionResult:
        if decision.status != "READY_FOR_EXECUTOR" or not decision.allowed:
            return RobotExecutionResult(sent=False, reason="Blocked by safety gate", executor="dry_run")
        return RobotExecutionResult(sent=True, reason=f"Dry run: would execute {skill.skill_type}", executor="dry_run", response=skill.model_dump())
