import cv2
import numpy as np
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.yolo_trainer import YOLOTrainer

class SecondaryObjectDetectionAgent(BaseAgent):
    """
    Second independent object detection agent operating on a half-resolution frame
    with a higher confidence threshold (0.45), creating architecture- and resolution-driven perceptual variance.
    """
    def __init__(self, yolo_trainer: Optional[YOLOTrainer] = None):
        super().__init__("Secondary Detection Agent")
        self.yolo_trainer = yolo_trainer or YOLOTrainer()

    def _analyze(self, image: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not isinstance(image, np.ndarray) or image.size == 0:
            return {
                "decision": "NO_OBSTACLE",
                "confidence": 0.80,
                "reasoning": "No valid image provided for secondary object detection.",
                "evidence": {"detections": []}
            }

        h, w = image.shape[0], image.shape[1]
        half_img = cv2.resize(image, (max(16, w // 2), max(16, h // 2)))

        # Predict on half-res image with threshold 0.45
        raw_detections = self.yolo_trainer.predict(half_img, conf_threshold=0.45)

        # Scale bounding boxes back to full image resolution
        detections = []
        for d in raw_detections:
            bbox = d.get("bbox", [0, 0, 0, 0])
            scaled_bbox = [bbox[0] * 2.0, bbox[1] * 2.0, bbox[2] * 2.0, bbox[3] * 2.0]
            d_copy = dict(d)
            d_copy["bbox"] = scaled_bbox
            detections.append(d_copy)

        has_pedestrian = any(d["class_name"] == "pedestrian" for d in detections)
        has_red_light = any(d["class_name"] == "traffic_light_red" for d in detections)
        has_green_light = any(d["class_name"] == "traffic_light_green" for d in detections)
        has_car_ahead = any(d["class_name"] == "car" for d in detections)
        has_obstacle = any(d["class_name"] == "obstacle" for d in detections)

        if has_pedestrian:
            decision = "PEDESTRIAN_DETECTED"
            confidence = 0.91
            reasoning = "Secondary agent (half-res, 0.45 conf) detected pedestrian in roadway."
        elif has_red_light:
            decision = "RED_LIGHT_DETECTED"
            confidence = 0.93
            reasoning = "Secondary agent detected RED traffic light."
        elif has_obstacle:
            decision = "OBSTACLE_AHEAD"
            confidence = 0.85
            reasoning = "Secondary agent detected hazard obstacle."
        elif has_car_ahead:
            decision = "VEHICLE_AHEAD"
            confidence = 0.88
            reasoning = "Secondary agent detected vehicle ahead."
        elif has_green_light:
            decision = "GREEN_LIGHT_DETECTED"
            confidence = 0.92
            reasoning = "Secondary agent detected GREEN traffic signal."
        else:
            decision = "ROAD_CLEAR"
            confidence = 0.86
            reasoning = "Secondary agent detected no obstacles on half-resolution view."

        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": {
                "detections": detections,
                "total_objects": len(detections),
                "resolution": f"{w//2}x{h//2}",
                "conf_threshold": 0.45,
                "has_pedestrian": has_pedestrian,
                "has_red_light": has_red_light,
                "has_green_light": has_green_light,
                "has_car_ahead": has_car_ahead
            }
        }
