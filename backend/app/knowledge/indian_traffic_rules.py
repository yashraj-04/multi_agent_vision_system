"""
Retrievable Knowledge Base for Indian Road Safety Regulations
Sources:
1. The Motor Vehicles Act, 1988 (MVA 1988) - Govt. of India
2. IRC:67-2012 - Code of Practice for Road Signs (Indian Roads Congress)
"""

from typing import Dict, Any, Optional, List

INDIAN_TRAFFIC_RULES_KB: Dict[str, Dict[str, Any]] = {
    "MVA_SEC_119_RED_SIGNAL": {
        "rule_id": "MVA_SEC_119_RED_SIGNAL",
        "title": "Mandatory Stop at Red Traffic Light / Stop Sign",
        "source": "Motor Vehicles Act 1988, Section 119 & IRC:67-2012 Clause 20.3",
        "scenario_tag": "traffic_signal_red",
        "rule_text": "Every driver of a motor vehicle shall satisfy himself that the driver of any vehicle behind him has understood his signal and shall obey the directions given by any mandatory traffic sign or red light signal.",
        "mandatory_action": "STOP",
        "priority_level": 1
    },
    "MVA_SEC_120_VULNERABLE_HAZARD": {
        "rule_id": "MVA_SEC_120_VULNERABLE_HAZARD",
        "title": "Emergency Obstacle & Vulnerable User Safety Override",
        "source": "Motor Vehicles Act 1988, Section 120 (Dangerous Driving Avoidance)",
        "scenario_tag": "vulnerable_user_in_path",
        "rule_text": "Drivers must maintain safe longitudinal headway and immediately execute emergency braking when vulnerable road users (pedestrians, bicycles, auto-rickshaws) enter the vehicle path.",
        "mandatory_action": "EMERGENCY BRAKE",
        "priority_level": 0
    },
    "IRC_67_CROSSWALK_CAUTION": {
        "rule_id": "IRC_67_CROSSWALK_CAUTION",
        "title": "Pedestrian Crossing & Intersection Approach Speed Limit",
        "source": "IRC:67-2012 Clause 16.2 (Pedestrian Cautionary Markings)",
        "scenario_tag": "pedestrian_crossing_approach",
        "rule_text": "Vehicles approaching a painted zebra crossing or marked pedestrian zone must reduce speed to allow safe passage for pedestrians.",
        "mandatory_action": "SLOW DOWN",
        "priority_level": 2
    },
    "MVA_SEC_184_ADVERSE_CONDITIONS": {
        "rule_id": "MVA_SEC_184_ADVERSE_CONDITIONS",
        "title": "Adverse Weather & Low-Light Speed Reduction",
        "source": "Motor Vehicles Act 1988, Section 184 (Weather/Visibility Safety)",
        "scenario_tag": "adverse_weather_night",
        "rule_text": "Driving in a speed or manner dangerous to the public under heavy rain, fog, or low visibility requires immediate speed deceleration below posted limits.",
        "mandatory_action": "SLOW DOWN",
        "priority_level": 2
    },
    "MVA_SEC_121_LANE_DISCIPLINE": {
        "rule_id": "MVA_SEC_121_LANE_DISCIPLINE",
        "title": "Mandatory Lane Discipline & Boundary Keeping",
        "source": "Motor Vehicles Act 1988, Section 121 & IRC:35-2015 Code of Road Markings",
        "scenario_tag": "lane_keeping",
        "rule_text": "Vehicle must remain strictly within marked lane boundaries unless signaling a safe lane change maneuver.",
        "mandatory_action": "PROCEED",
        "priority_level": 3
    },
    "MVA_SEC_119_GREEN_SIGNAL": {
        "rule_id": "MVA_SEC_119_GREEN_SIGNAL",
        "title": "Green Light Proceed with Intersection Vigilance",
        "source": "Motor Vehicles Act 1988, Section 119 & IRC:67-2012 Clause 20.1",
        "scenario_tag": "green_light_proceed",
        "rule_text": "Green signal indicates permission to proceed straight or turn, provided the intersection is clear of obstructing traffic.",
        "mandatory_action": "PROCEED",
        "priority_level": 3
    }
}

def retrieve_rule_by_scenario(scenario_tag: str) -> Dict[str, Any]:
    """Retrieve Indian traffic rule by scenario keyword or return general safety default."""
    for rule_id, rule_info in INDIAN_TRAFFIC_RULES_KB.items():
        if rule_info["scenario_tag"] == scenario_tag:
            return rule_info
    
    # Fallback to general MVA Section 120 safety rule
    return INDIAN_TRAFFIC_RULES_KB["MVA_SEC_120_VULNERABLE_HAZARD"]

def generate_rejection_rationale(candidate_action: str, winning_action: str, rule_info: Dict[str, Any]) -> str:
    """Generate explicit natural language rationale for why a candidate action was rejected."""
    if candidate_action == winning_action:
        return "Action selected as optimal arbitrated decision."

    rule_source = rule_info.get("source", "MVA 1988 Safety Standards")
    rule_title = rule_info.get("title", "Safety Rule")

    if winning_action == "EMERGENCY BRAKE":
        return f"'{candidate_action}' rejected: Immediate safety override mandatory under {rule_source} ({rule_title}) due to critical obstacle/pedestrian proximity."
    elif winning_action == "STOP":
        return f"'{candidate_action}' rejected: Statutory stop requirement under {rule_source} ({rule_title}) overrides permissive actions."
    elif winning_action == "SLOW DOWN":
        return f"'{candidate_action}' rejected: Speed reduction required under {rule_source} ({rule_title}) due to cautionary road conditions or pedestrian crosswalk approach."
    elif winning_action == "PROCEED":
        return f"'{candidate_action}' rejected: Excessive restrictive braking unneeded as road path is clear according to {rule_source}."

    return f"'{candidate_action}' rejected in favor of '{winning_action}' based on rule priority hierarchy in {rule_source}."
