"""
Agent Registry and Specification Schema.
Defines formal mapping for all independent perception and meta agents:
- Trigger Condition
- Required Input
- Output Vocabulary
- Standalone Execution Status
"""

from typing import Dict, Any, List

AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "Object Detection Agent": {
        "agent_name": "Object Detection Agent",
        "description": "Primary YOLOv8 detector operating on full-resolution optical input.",
        "trigger_condition": "Always active on new frame intake.",
        "required_input": "Raw RGB/BGR Image array (h x w x 3)",
        "output_vocabulary": ["GO", "SLOW DOWN", "EMERGENCY BRAKE", "STOP"],
        "confidence_threshold": 0.30,
        "standalone_execution": True,
        "primary_modalities": ["Bounding Boxes", "Distance Estimation", "TTC"]
    },
    "Secondary Object Detection Agent": {
        "agent_name": "Secondary Object Detection Agent",
        "description": "Independent secondary YOLOv8 detector operating on half-resolution view for multi-scale perceptual diversity.",
        "trigger_condition": "Always active on new frame intake.",
        "required_input": "Half-resolution image array (w//2, h//2)",
        "output_vocabulary": ["GO", "SLOW DOWN", "EMERGENCY BRAKE", "STOP"],
        "confidence_threshold": 0.45,
        "standalone_execution": True,
        "primary_modalities": ["Multi-scale Bounding Boxes", "Coarse Object Spatial Verification"]
    },
    "Lane Detection Agent": {
        "agent_name": "Lane Detection Agent",
        "description": "Classical Computer Vision lane boundary, departure, and curvature estimator.",
        "trigger_condition": "Always active on new frame intake.",
        "required_input": "Raw RGB/BGR Image array (h x w x 3)",
        "output_vocabulary": ["MAINTAIN LANE", "CHANGE LANE LEFT", "CHANGE LANE RIGHT", "SLOW DOWN"],
        "confidence_threshold": 0.50,
        "standalone_execution": True,
        "primary_modalities": ["Lane Curvature", "Vehicle Center Offset", "Vanishing Point"]
    },
    "Traffic Rule Agent": {
        "agent_name": "Traffic Rule Agent",
        "description": "Independent Traffic Light and Road Sign Rule Reasoning Agent grounded in MVA 1988 & IRC:67-2012.",
        "trigger_condition": "Active when traffic signs, signals, or intersections are detected.",
        "required_input": "Raw RGB/BGR Image array (h x w x 3)",
        "output_vocabulary": ["MUST_STOP_RED_LIGHT", "SLOW_DOWN_CROSSWALK", "PROCEED_GREEN_LIGHT"],
        "confidence_threshold": 0.50,
        "standalone_execution": True,
        "primary_modalities": ["Signal Aspect HSV Detection", "Sign Box Geometry", "Statutory Rule Matching"]
    },
    "Scene Understanding Agent": {
        "agent_name": "Scene Understanding Agent",
        "description": "Multimodal VisionLLM for holistic environmental, weather, and occluded hazard analysis.",
        "trigger_condition": "Active on frame intake or environment caution request.",
        "required_input": "Raw RGB/BGR Image array (h x w x 3)",
        "output_vocabulary": ["NORMAL_ENVIRONMENT", "ADVERSE_WEATHER_CAUTION", "ROADWAY_OBSTRUCTION", "HAZARD_POTENTIAL_DETECTED"],
        "confidence_threshold": 0.85,
        "standalone_execution": True,
        "primary_modalities": ["Environmental Weather", "Illumination", "VLM Semantic Context"]
    },
    "Risk Assessment Agent": {
        "agent_name": "Risk Assessment Agent",
        "description": "High-recall probabilistic risk and collision threat assessor.",
        "trigger_condition": "Always active on new frame intake.",
        "required_input": "Raw RGB/BGR Image array (h x w x 3)",
        "output_vocabulary": ["EMERGENCY_BRAKE_CRITICAL_RISK", "SLOW_DOWN_HIGH_RISK", "CAUTION_MONITOR", "SAFE_LOW_RISK"],
        "confidence_threshold": 0.25,
        "standalone_execution": True,
        "primary_modalities": ["Time-To-Collision (TTC)", "Proximity Density", "Deceleration Profile"]
    },
    "Centralized Planner": {
        "agent_name": "Centralized Planner",
        "description": "Monolithic trajectory planner baseline operating outside the voting pool.",
        "trigger_condition": "Baseline comparison mode.",
        "required_input": "Perception agent outputs array",
        "output_vocabulary": ["GO", "SLOW DOWN", "STOP", "EMERGENCY BRAKE"],
        "confidence_threshold": 0.90,
        "standalone_execution": False,
        "primary_modalities": ["Centralized Rule Evaluation"]
    },
    "Strategy Selector Agent": {
        "agent_name": "Strategy Selector Agent",
        "description": "Meta-Orchestrator selecting the optimal conflict resolution strategy.",
        "trigger_condition": "Active during dynamic arbitration.",
        "required_input": "Voting pool outputs + Conflict list",
        "output_vocabulary": ["Majority Voting", "Confidence Weighted Voting", "Rule-Based Arbitration", "Leader Election"],
        "confidence_threshold": 0.92,
        "standalone_execution": False,
        "primary_modalities": ["Meta-level Conflict Severity & Disagreement Analysis"]
    }
}

def get_agent_registry() -> Dict[str, Dict[str, Any]]:
    return AGENT_REGISTRY
