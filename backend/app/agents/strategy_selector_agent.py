from typing import Dict, Any, List, Optional
from app.agents.base_agent import BaseAgent, AgentOutput

def _get(obj: Any, attr: str, default: Any = None) -> Any:
    if hasattr(obj, attr):
        return getattr(obj, attr)
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return default

class StrategySelectorAgent(BaseAgent):
    """
    Meta-Orchestrator Agent that dynamically evaluates perception outputs, agent confidences,
    and hazard severity to automatically select the optimal Conflict Resolution Strategy out of 4 core strategies:
    1. Majority Voting
    2. Confidence Weighted Voting
    3. Rule-Based Arbitration
    4. Leader Election
    """
    def __init__(self):
        super().__init__("Strategy Selector Agent")

    def _analyze(self, image: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prior_outputs = context.get("prior_agent_outputs", []) if context else []
        conflicts = context.get("conflicts", []) if context else []

        # Check for critical safety hazards or rule violations
        has_critical_conflict = any(_get(c, "severity") == "CRITICAL" for c in conflicts)
        risk_agent = next((a for a in prior_outputs if _get(a, "agent_name") == "Risk Assessment Agent"), None)
        rule_agent = next((a for a in prior_outputs if _get(a, "agent_name") == "Traffic Rule Agent"), None)
        
        risk_decision = _get(risk_agent, "decision", "") if risk_agent else ""
        rule_decision = _get(rule_agent, "decision", "") if rule_agent else ""

        # Extract agent confidences
        confidences = [_get(a, "confidence", 0.8) for a in prior_outputs]
        max_conf = max(confidences) if confidences else 0.85
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.85
        
        # Rule 1: High Safety Hazard or Rule Violation -> Rule-Based Arbitration
        if has_critical_conflict or risk_decision in ["IMMINENT_COLLISION_WARNING", "HIGH_RISK_WARNING"] or rule_decision in ["MUST_STOP_RED_LIGHT", "MUST_STOP_SIGN"]:
            selected_strategy = "Rule-Based Arbitration"
            confidence = 0.98
            reasoning = "Rule-Based Arbitration automatically selected due to CRITICAL safety risk or mandatory traffic rule compliance."
        
        # Rule 2: Single Dominant Agent (>95% confidence) -> Leader Election
        elif max_conf >= 0.95 and (max_conf - avg_conf) > 0.10:
            selected_strategy = "Leader Election"
            confidence = 0.94
            reasoning = f"Leader Election automatically selected because a primary perception agent demonstrated dominant confidence ({max_conf * 100:.1f}%)."

        # Rule 3: High variance in agent confidences -> Confidence Weighted Voting
        elif (max_conf - min(confidences) if confidences else 0) > 0.15:
            selected_strategy = "Confidence Weighted Voting"
            confidence = 0.91
            reasoning = "Confidence Weighted Voting automatically selected to weight agent proposals by individual certainty metrics."

        # Rule 4: Balanced confidences & low conflict -> Majority Voting
        else:
            selected_strategy = "Majority Voting"
            confidence = 0.89
            reasoning = "Majority Voting automatically selected as all perception agents demonstrate balanced consensus."

        return {
            "decision": selected_strategy,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": {
                "selected_strategy": selected_strategy,
                "has_critical_conflict": has_critical_conflict,
                "max_agent_confidence": round(max_conf, 3),
                "conflict_count": len(conflicts),
                "supported_4_strategies": [
                    "Majority Voting",
                    "Confidence Weighted Voting",
                    "Rule-Based Arbitration",
                    "Leader Election"
                ]
            }
        }
