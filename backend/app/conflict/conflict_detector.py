from typing import List, Dict, Any, Union
from app.agents.base_agent import AgentOutput
from app.utils.logger import logger

def _get_field(item: Any, field_name: str, default: Any = None) -> Any:
    if hasattr(item, field_name):
        val = getattr(item, field_name)
        if val is not None:
            return val
    if isinstance(item, dict):
        return item.get(field_name, default)
    return default

def normalize_to_canonical_action(decision: str) -> str:
    """Maps agent specific decisions to closed canonical action set."""
    if not decision:
        return None
    d = str(decision).strip().upper()
    mapping = {
        "GO": "GO",
        "PROCEED": "GO",
        "ROAD_CLEAR": "GO",
        "NO_OBSTACLE": "GO",
        "GREEN_LIGHT_DETECTED": "GO",
        "PROCEED_GREEN_LIGHT": "GO",
        "STANDARD_RIGHT_OF_WAY": "GO",
        "LANE_CENTERED": "GO",
        "NORMAL_ENVIRONMENT": "GO",
        "LOW_RISK": "GO",

        "SLOW DOWN": "SLOW DOWN",
        "SLOW": "SLOW DOWN",
        "REDUCE SPEED": "SLOW DOWN",
        "PEDESTRIAN_DETECTED": "SLOW DOWN",
        "OBSTACLE_AHEAD": "SLOW DOWN",
        "HIGH_RISK_WARNING": "SLOW DOWN",
        "MODERATE_RISK": "SLOW DOWN",
        "ADVERSE_WEATHER_CAUTION": "SLOW DOWN",
        "HAZARD_POTENTIAL_DETECTED": "SLOW DOWN",
        "ROADWAY_OBSTRUCTION": "SLOW DOWN",

        "STOP": "STOP",
        "MUST_STOP_RED_LIGHT": "STOP",
        "MUST_STOP_SIGN": "STOP",
        "RED_LIGHT_DETECTED": "STOP",

        "EMERGENCY BRAKE": "EMERGENCY BRAKE",
        "EMERGENCY_BRAKE": "EMERGENCY BRAKE",
        "IMMINENT_COLLISION_WARNING": "EMERGENCY BRAKE",

        "TURN LEFT": "TURN LEFT",
        "CURVE_LEFT": "TURN LEFT",

        "TURN RIGHT": "TURN RIGHT",
        "CURVE_RIGHT": "TURN RIGHT",

        "CHANGE LANE": "CHANGE LANE",
        "VEHICLE_AHEAD": "CHANGE LANE",
        "LANE_DEPARTURE_WARNING": "CHANGE LANE"
    }
    return mapping.get(d, None)

ACTION_LONGITUDINAL_INDEX = {
    "GO": 0,
    "TURN LEFT": 0,
    "TURN RIGHT": 0,
    "CHANGE LANE": 0,
    "SLOW DOWN": 1,
    "STOP": 2,
    "EMERGENCY BRAKE": 3
}

class ConflictDetector:
    """
    Scans agent outputs to identify semantic, safety, or rule contradictions, plus generic action space divergence.
    """
    def detect_conflicts(self, agent_outputs: List[Union[AgentOutput, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        conflicts = []
        outputs_by_name = {}
        for a in agent_outputs:
            name = _get_field(a, "agent_name")
            if name:
                outputs_by_name[name] = a

        obj = outputs_by_name.get("Object Detection Agent")
        sec_obj = outputs_by_name.get("Secondary Detection Agent")
        lane = outputs_by_name.get("Lane Detection Agent")
        rule = outputs_by_name.get("Traffic Rule Agent")
        scene = outputs_by_name.get("Scene Understanding Agent")
        risk = outputs_by_name.get("Risk Assessment Agent")
        plan = outputs_by_name.get("Planning Agent")

        # 1. Traffic Signal Conflict
        if obj and rule:
            evidence = _get_field(obj, "evidence", {})
            obj_det = evidence.get("has_green_light", False) if isinstance(evidence, dict) else False
            rule_dec = _get_field(rule, "decision", "")
            rule_stop = rule_dec in ["MUST_STOP_RED_LIGHT", "MUST_STOP_SIGN"]
            if obj_det and rule_stop:
                conflicts.append({
                    "id": f"C_SIG_{len(conflicts)+1}",
                    "type": "Traffic Signal Disagreement",
                    "severity": "CRITICAL",
                    "agents": ["Object Detection Agent", "Traffic Rule Agent"],
                    "description": f"Object Agent detected Green Light (Conf: {_get_field(obj, 'confidence', 0.9)}), but Traffic Rule Agent commands mandatory STOP (Conf: {_get_field(rule, 'confidence', 0.9)}).",
                    "competing_proposals": {
                        "Object Detection Agent": "PROCEED / GREEN",
                        "Traffic Rule Agent": rule_dec
                    }
                })

        # 2. Obstacle / Hazard Perception Conflict
        if obj and scene:
            obj_dec = _get_field(obj, "decision", "")
            scene_dec = _get_field(scene, "decision", "")
            no_obj = obj_dec in ["ROAD_CLEAR", "NO_OBSTACLE"]
            scene_hazard = scene_dec in ["ROADWAY_OBSTRUCTION", "HAZARD_POTENTIAL_DETECTED"]
            if no_obj and scene_hazard:
                conflicts.append({
                    "id": f"C_OBS_{len(conflicts)+1}",
                    "type": "Obstacle Detection Mismatch",
                    "severity": "HIGH",
                    "agents": ["Object Detection Agent", "Scene Understanding Agent"],
                    "description": f"Object Agent reports clear road, but Scene Understanding (VisionLLM) flagged environmental hazard: {_get_field(scene, 'reasoning', '')}",
                    "competing_proposals": {
                        "Object Detection Agent": "ROAD_CLEAR",
                        "Scene Understanding Agent": scene_dec
                    }
                })

        # 3. Path Safety vs Lane Clearance Conflict
        if lane and risk:
            lane_dec = _get_field(lane, "decision", "")
            risk_dec = _get_field(risk, "decision", "")
            risk_ev = _get_field(risk, "evidence", {})
            ttc = risk_ev.get("time_to_collision_sec", "N/A") if isinstance(risk_ev, dict) else "N/A"
            lane_centered = lane_dec == "LANE_CENTERED"
            risk_high = risk_dec in ["IMMINENT_COLLISION_WARNING", "HIGH_RISK_WARNING"]
            if lane_centered and risk_high:
                conflicts.append({
                    "id": f"C_RISK_{len(conflicts)+1}",
                    "type": "Path Safety & Risk Contradiction",
                    "severity": "CRITICAL",
                    "agents": ["Lane Detection Agent", "Risk Assessment Agent"],
                    "description": f"Lane Agent reports stable lane geometry, but Risk Agent warns of {risk_dec} (TTC: {ttc}s).",
                    "competing_proposals": {
                        "Lane Detection Agent": "MAINTAIN LANE / GO",
                        "Risk Assessment Agent": "BRAKE / SLOW"
                    }
                })

        # 4. Traffic Rule vs Weather Hazard Conflict (Driven from Scene Weather Output)
        if rule and scene:
            rule_dec = _get_field(rule, "decision", "")
            scene_dec = _get_field(scene, "decision", "")
            rule_go = rule_dec in ["STANDARD_RIGHT_OF_WAY", "PROCEED_GREEN_LIGHT"]
            adverse_weather = scene_dec in ["ADVERSE_WEATHER_CAUTION", "ROADWAY_OBSTRUCTION"]
            if rule_go and adverse_weather:
                conflicts.append({
                    "id": f"C_SPD_{len(conflicts)+1}",
                    "type": "Speed Limit & Environmental Safety Conflict",
                    "severity": "MEDIUM",
                    "agents": ["Traffic Rule Agent", "Scene Understanding Agent"],
                    "description": "Traffic Rule permits normal cruising, but Scene Agent indicates reduced traction weather requiring speed reduction.",
                    "competing_proposals": {
                        "Traffic Rule Agent": rule_dec,
                        "Scene Understanding Agent": scene_dec
                    }
                })

        # 5. Planning Action Disagreement with Risk Assessment
        if plan and risk:
            plan_dec = _get_field(plan, "decision", "")
            risk_dec = _get_field(risk, "decision", "")
            plan_go = plan_dec in ["GO", "CHANGE LANE"]
            risk_danger = risk_dec in ["IMMINENT_COLLISION_WARNING", "HIGH_RISK_WARNING"]
            if plan_go and risk_danger:
                conflicts.append({
                    "id": f"C_PLAN_{len(conflicts)+1}",
                    "type": "Planner & Risk Assessment Mismatch",
                    "severity": "CRITICAL",
                    "agents": ["Planning Agent", "Risk Assessment Agent"],
                    "description": f"Planner proposed '{plan_dec}', contradicting Risk Agent high hazard warning.",
                    "competing_proposals": {
                        "Planning Agent": plan_dec,
                        "Risk Assessment Agent": "EMERGENCY BRAKE"
                    }
                })

        # =========================================================================
        # 6. Generic Conflict Detector: Action Space Divergence
        # =========================================================================
        agent_actions = {}
        for a in agent_outputs:
            name = _get_field(a, "agent_name")
            dec = _get_field(a, "decision")
            act = normalize_to_canonical_action(dec)
            if name and act and name not in ["Planning Agent", "Strategy Selector Agent"]:
                agent_actions[name] = act

        unique_actions = set(agent_actions.values())
        if len(unique_actions) > 1:
            indices = [ACTION_LONGITUDINAL_INDEX.get(act, 0) for act in unique_actions]
            gap = max(indices) - min(indices)
            if gap >= 3:
                sev = "CRITICAL"
            elif gap == 2:
                sev = "HIGH"
            else:
                sev = "LOW"

            conflicts.append({
                "id": f"C_DIV_{len(conflicts)+1}",
                "type": "Action Space Divergence",
                "severity": sev,
                "agents": list(agent_actions.keys()),
                "description": f"Perception agents proposed {len(unique_actions)} distinct canonical actions: {sorted(list(unique_actions))}.",
                "competing_proposals": agent_actions
            })

        logger.info(f"Conflict Detector identified {len(conflicts)} conflict event(s).")
        return conflicts
