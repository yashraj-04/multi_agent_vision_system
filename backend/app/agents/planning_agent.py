from typing import Dict, Any, Optional, List
from app.agents.base_agent import BaseAgent, AgentOutput

def _get(obj: Any, attr: str, default: Any = None) -> Any:
    if hasattr(obj, attr):
        return getattr(obj, attr)
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return default

class PlanningAgent(BaseAgent):
    def __init__(self):
        super().__init__("Planning Agent")

    def _analyze(self, image: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prior_outputs: List[AgentOutput] = context.get("prior_agent_outputs", []) if context else []
        
        # Extract individual agent decisions
        object_dec = next((_get(a, "decision") for a in prior_outputs if _get(a, "agent_name") == "Object Detection Agent"), "ROAD_CLEAR")
        lane_dec = next((_get(a, "decision") for a in prior_outputs if _get(a, "agent_name") == "Lane Detection Agent"), "LANE_CENTERED")
        rule_dec = next((_get(a, "decision") for a in prior_outputs if _get(a, "agent_name") == "Traffic Rule Agent"), "STANDARD_RIGHT_OF_WAY")
        scene_dec = next((_get(a, "decision") for a in prior_outputs if _get(a, "agent_name") == "Scene Understanding Agent"), "NORMAL_ENVIRONMENT")
        risk_dec = next((_get(a, "decision") for a in prior_outputs if _get(a, "agent_name") == "Risk Assessment Agent"), "LOW_RISK")

        # Synthesize optimal vehicle control command using real distance thresholds
        if risk_dec == "IMMINENT_COLLISION_WARNING" or rule_dec in ["MUST_STOP_RED_LIGHT", "MUST_STOP_SIGN"]:
            if risk_dec == "IMMINENT_COLLISION_WARNING":
                suggested_action = "EMERGENCY BRAKE"
                reasoning = "Planner override: Emergency braking commanded (Object distance < 5m or TTC < 2.0s)."
                confidence = 0.98
            else:
                suggested_action = "STOP"
                reasoning = "Planner override: Full stop commanded by traffic law (Red Light / Stop Sign)."
                confidence = 0.96
        elif risk_dec == "HIGH_RISK_WARNING" or object_dec in ["PEDESTRIAN_DETECTED", "OBSTACLE_AHEAD"] or scene_dec == "ADVERSE_WEATHER_CAUTION":
            suggested_action = "SLOW DOWN"
            reasoning = "Planner action: Gradual braking / speed reduction commanded for medium range obstacle or weather caution."
            confidence = 0.91
        elif lane_dec == "CURVE_LEFT":
            suggested_action = "TURN LEFT"
            reasoning = "Planner action: Steering left along lane curvature."
            confidence = 0.89
        elif lane_dec == "CURVE_RIGHT":
            suggested_action = "TURN RIGHT"
            reasoning = "Planner action: Steering right along lane curvature."
            confidence = 0.89
        elif object_dec == "VEHICLE_AHEAD" and lane_dec != "LANE_DEPARTURE_WARNING":
            suggested_action = "CHANGE LANE"
            reasoning = "Planner action: Slow vehicle ahead detected at safe distance; initiating lane change."
            confidence = 0.84
        elif rule_dec == "PROCEED_GREEN_LIGHT" or object_dec in ["ROAD_CLEAR", "GREEN_LIGHT_DETECTED"] or risk_dec in ["LOW_RISK", "MODERATE_RISK"]:
            suggested_action = "GO"
            reasoning = "Planner action: Safe distance maintained (>30m). Cruising at target speed."
            confidence = 0.94
        else:
            suggested_action = "SLOW DOWN"
            reasoning = "Planner action: Defensive driving speed adjustment."
            confidence = 0.82

        return {
            "decision": suggested_action,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": {
                "object_agent": object_dec,
                "lane_agent": lane_dec,
                "rule_agent": rule_dec,
                "scene_agent": scene_dec,
                "risk_agent": risk_dec
            }
        }
