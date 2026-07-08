from typing import Literal

from pydantic import BaseModel


class RiskEvidence(BaseModel):
    simulations: int
    failures: int


class RiskReport(BaseModel):
    decision: Literal["ALLOW", "CAUTION", "BLOCK"]
    risk_percent: int
    reason: str
    evidence: RiskEvidence
