from foresight.decision.risk_report import RiskEvidence, RiskReport


class SafetyGate:
    def __init__(self, block_threshold: float = 0.30):
        self.block_threshold = block_threshold

    def decide(
        self,
        failures: int,
        simulations: int,
        reason: str = "Predicted physical failure",
    ) -> RiskReport:
        if simulations <= 0:
            return RiskReport(
                decision="BLOCK",
                risk_percent=100,
                reason="No valid simulations available",
                evidence=RiskEvidence(simulations=0, failures=0),
            )

        risk = failures / simulations
        risk_percent = round(risk * 100)
        if risk > self.block_threshold:
            decision = "BLOCK"
        elif risk > self.block_threshold / 2:
            decision = "CAUTION"
        else:
            decision = "ALLOW"

        return RiskReport(
            decision=decision,
            risk_percent=risk_percent,
            reason=reason,
            evidence=RiskEvidence(simulations=simulations, failures=failures),
        )
