from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.vision_llm import VisionLLM

class SceneUnderstandingAgent(BaseAgent):
    def __init__(self, vision_llm: Optional[VisionLLM] = None):
        super().__init__("Scene Understanding Agent")
        self.vision_llm = vision_llm or VisionLLM()

    def _analyze(self, image: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        object_detections = []  # Decoupled independent perception

        # Call VisionLLM abstraction layer
        scene_analysis = self.vision_llm.analyze_scene(image)
        verification = self.vision_llm.verify_detection(image, object_detections)
        hidden_risk = self.vision_llm.estimate_hidden_risk(image, object_detections)

        weather = scene_analysis.get("weather", "Clear")
        unusual = scene_analysis.get("unusual_situations", "None")
        desc = scene_analysis.get("scene_description", "Standard road traffic flow.")

        if hidden_risk.get("hidden_risk_detected", False):
            decision = "HAZARD_POTENTIAL_DETECTED"
            confidence = 0.86
            reasoning = f"VisionLLM detected elevated environmental risk: {hidden_risk.get('description')}"
        elif "rain" in weather.lower() or "fog" in weather.lower():
            decision = "ADVERSE_WEATHER_CAUTION"
            confidence = 0.88
            reasoning = f"Weather condition '{weather}' reduces traction and optical range."
        elif "hazard" in unusual.lower() or "blocked" in unusual.lower():
            decision = "ROADWAY_OBSTRUCTION"
            confidence = 0.90
            reasoning = f"Semantic scene interpretation indicates roadway anomaly: {unusual}"
        else:
            decision = "NORMAL_ENVIRONMENT"
            confidence = 0.92
            reasoning = f"VLM Analysis: {desc}"

        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": {
                "vision_model": self.vision_llm.model_name,
                "weather": weather,
                "road_condition": scene_analysis.get("road_condition", "Dry"),
                "unusual_situations": unusual,
                "vlm_verification": verification.get("vlm_feedback"),
                "hidden_risk": hidden_risk
            }
        }
