from typing import Dict, Any, Optional
import numpy as np
from app.agents.base_agent import BaseAgent
from app.yolo_trainer import YOLOTrainer

class ObjectDetectionAgent(BaseAgent):
    def __init__(self, yolo_trainer: Optional[YOLOTrainer] = None):
        super().__init__("Object Detection Agent")
        self.yolo_trainer = yolo_trainer or YOLOTrainer()

    def _analyze(self, image: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not isinstance(image, np.ndarray):
            return {
                "decision": "NO_OBSTACLE",
                "confidence": 0.85,
                "reasoning": "No valid image provided for object detection.",
                "evidence": {"detections": []}
            }
            
        detections = self.yolo_trainer.predict(image)
        
        # Analyze detections to produce primary decision
        has_pedestrian = any(d["class_name"] == "pedestrian" for d in detections)
        has_red_light = any(d["class_name"] == "traffic_light_red" for d in detections)
        has_green_light = any(d["class_name"] == "traffic_light_green" for d in detections)
        has_car_ahead = any(d["class_name"] == "car" for d in detections)
        has_obstacle = any(d["class_name"] == "obstacle" for d in detections)
        
        if has_pedestrian:
            decision = "PEDESTRIAN_DETECTED"
            confidence = 0.94
            reasoning = f"Detected {sum(1 for d in detections if d['class_name']=='pedestrian')} pedestrian(s) in roadway."
        elif has_red_light:
            decision = "RED_LIGHT_DETECTED"
            confidence = 0.96
            reasoning = "Traffic light signal detected as RED."
        elif has_obstacle:
            decision = "OBSTACLE_AHEAD"
            confidence = 0.88
            reasoning = "Static/Dynamic hazard obstacle detected directly in trajectory."
        elif has_car_ahead:
            decision = "VEHICLE_AHEAD"
            confidence = 0.90
            reasoning = "Vehicle ahead detected in current travel corridor."
        elif has_green_light:
            decision = "GREEN_LIGHT_DETECTED"
            confidence = 0.95
            reasoning = "Traffic signal clear GREEN."
        else:
            decision = "ROAD_CLEAR"
            confidence = 0.89
            reasoning = "No relevant static or dynamic obstacles detected."

        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": {
                "detections": detections,
                "total_objects": len(detections),
                "has_pedestrian": has_pedestrian,
                "has_red_light": has_red_light,
                "has_green_light": has_green_light,
                "has_car_ahead": has_car_ahead
            }
        }
