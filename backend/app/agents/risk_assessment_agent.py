from typing import Dict, Any, Optional
import numpy as np
from app.agents.base_agent import BaseAgent
from app.yolo_trainer import YOLOTrainer

class RiskAssessmentAgent(BaseAgent):
    """
    Independent Risk Assessment Agent operating at a high-recall confidence threshold (0.25).
    Performs dynamic distance estimation and Time-To-Collision (TTC) calculations independently.
    """
    def __init__(self, yolo_trainer: Optional[YOLOTrainer] = None):
        super().__init__("Risk Assessment Agent")
        self.yolo_trainer = yolo_trainer or YOLOTrainer()

    def _analyze(self, image: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        object_detections = []
        if isinstance(image, np.ndarray) and image.size > 0:
            object_detections = self.yolo_trainer.predict(image, conf_threshold=0.25)

        current_speed_kph = context.get("speed_kph", 50.0) if context else 50.0
        speed_m_s = current_speed_kph / 3.6  # Convert km/h to m/s

        h, w = 480, 640
        if isinstance(image, np.ndarray) and image.size > 0:
            h, w = image.shape[0], image.shape[1]

        min_distance_m = 100.0
        closest_object_class = None
        closest_bbox = None
        pedestrian_in_critical_zone = False
        obstacle_in_medium_range = False

        real_heights = {
            "car": 1.5, "vehicles": 1.5, "buses": 2.8, "pedestrian": 1.7,
            "motorcycles": 1.2, "bicycles": 1.1, "traffic_light_red": 0.8,
            "traffic_light_green": 0.8, "stop_sign": 0.9, "obstacle": 1.0
        }

        for d in object_detections:
            conf = d.get("confidence", 0.0)
            if conf < 0.35:
                continue

            bbox = d.get("bbox", [0, 0, 0, 0])
            if len(bbox) != 4:
                continue

            box_h = bbox[3] - bbox[1]
            if box_h <= 15:
                continue

            cls_name = d.get("class_name", "car").lower()
            obj_real_h = real_heights.get(cls_name, 1.5)

            focal_length_px = (w / 640.0) * 600.0
            est_dist = round((focal_length_px * obj_real_h) / float(box_h), 2)
            est_dist = max(2.0, min(120.0, est_dist))

            if est_dist < min_distance_m:
                min_distance_m = est_dist
                closest_object_class = d.get("class_name", "object")
                closest_bbox = bbox

            if ("pedestrian" in cls_name or "person" in cls_name) and est_dist < 4.0:
                pedestrian_in_critical_zone = True
            elif est_dist < 12.0:
                obstacle_in_medium_range = True

        ttc_sec = round(min_distance_m / max(speed_m_s, 0.1), 2) if min_distance_m < 100.0 else 99.9

        if min_distance_m < 3.0 or ttc_sec < 1.2 or pedestrian_in_critical_zone:
            collision_prob = 0.95
            emergency_level = "CRITICAL"
            decision = "IMMINENT_COLLISION_WARNING"
            reasoning = f"CRITICAL DANGER: Closest {closest_object_class or 'obstacle'} at {min_distance_m}m (TTC: {ttc_sec}s < 1.2s). Immediate emergency braking required!"
        elif min_distance_m < 12.0 or ttc_sec < 3.0 or obstacle_in_medium_range:
            collision_prob = 0.60
            emergency_level = "HIGH"
            decision = "HIGH_RISK_WARNING"
            reasoning = f"HIGH RISK: Closest {closest_object_class or 'obstacle'} at {min_distance_m}m (TTC: {ttc_sec}s). Gradual speed reduction recommended."
        elif min_distance_m < 25.0 or ttc_sec < 5.0:
            collision_prob = 0.25
            emergency_level = "MODERATE"
            decision = "MODERATE_RISK"
            reasoning = f"MODERATE DISTANCE: Closest object detected at {min_distance_m}m (TTC: {ttc_sec}s). Maintaining safe tracking gap."
        else:
            collision_prob = 0.05
            emergency_level = "LOW"
            decision = "LOW_RISK"
            reasoning = f"SAFE DISTANCE: Road clear. Closest object at {min_distance_m}m (TTC: {ttc_sec}s > 5.0s)."

        return {
            "decision": decision,
            "confidence": 0.96 if emergency_level in ["CRITICAL", "HIGH"] else 0.88,
            "reasoning": reasoning,
            "evidence": {
                "collision_probability": collision_prob,
                "estimated_min_distance_m": min_distance_m,
                "time_to_collision_sec": ttc_sec,
                "closest_object": closest_object_class,
                "closest_bbox": closest_bbox,
                "speed_kph": current_speed_kph,
                "conf_threshold": 0.25,
                "pedestrian_risk": pedestrian_in_critical_zone,
                "emergency_level": emergency_level
            }
        }
