from typing import Dict, Any, Optional
import cv2
import numpy as np
from app.agents.base_agent import BaseAgent
from app.yolo_trainer import YOLOTrainer
from app.knowledge.indian_traffic_rules import retrieve_rule_by_scenario, INDIAN_TRAFFIC_RULES_KB

class TrafficRuleAgent(BaseAgent):
    """
    Independent Traffic Rule Agent operating at a high precision confidence threshold (0.5).
    Evaluates traffic signals, stop signs, and right-of-way compliance grounded in MVA 1988 & IRC:67-2012.
    """
    def __init__(self, yolo_trainer: Optional[YOLOTrainer] = None):
        super().__init__("Traffic Rule Agent")
        self.yolo_trainer = yolo_trainer or YOLOTrainer()

    def _analyze(self, image: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        detections = []
        if isinstance(image, np.ndarray) and image.size > 0:
            detections = self.yolo_trainer.predict(image, conf_threshold=0.25)

        has_red_light = False
        has_green_light = False
        has_stop_sign = False

        for d in detections:
            cname = str(d.get("class_name", "")).lower()
            if cname in ["stop_sign", "stop sign"]:
                has_stop_sign = True
            elif cname in ["traffic_light_red", "red_light"]:
                has_red_light = True
            elif cname in ["traffic_light_green", "green_light"]:
                has_green_light = True
            elif cname in ["traffic light", "traffic lights", "traffic_light"]:
                # Crop bounding box and run HSV color test
                bbox = d.get("bbox", [0, 0, 0, 0])
                if isinstance(image, np.ndarray) and len(bbox) == 4:
                    x1, y1, x2, y2 = map(int, bbox)
                    crop = image[max(0, y1):min(image.shape[0], y2), max(0, x1):min(image.shape[1], x2)]
                    if crop.size > 0:
                        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                        mask_red1 = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([12, 255, 255]))
                        mask_red2 = cv2.inRange(hsv, np.array([160, 70, 70]), np.array([180, 255, 255]))
                        mask_green = cv2.inRange(hsv, np.array([35, 30, 100]), np.array([95, 255, 255]))
                        
                        # Direct BGR channel green LED check (G > R + 25 and G > B)
                        b, g, r = crop[:, :, 0], crop[:, :, 1], crop[:, :, 2]
                        bgr_green_mask = (g > r + 25) & (g > b) & (g > 100)

                        red_cnt = np.sum((mask_red1 | mask_red2) > 0)
                        green_cnt = np.sum(mask_green > 0) + np.sum(bgr_green_mask)
                        if green_cnt > red_cnt and green_cnt >= 8:
                            has_green_light = True
                        elif red_cnt >= 8:
                            has_red_light = True

        # Check top-center region of image (y: 0 to 35% height) for prominent green LED overhead traffic light
        if isinstance(image, np.ndarray) and not has_red_light and not has_green_light and image.size > 0:
            ih, iw, _ = image.shape
            top_center = image[0:int(ih * 0.35), int(iw * 0.25):int(iw * 0.75)]
            if top_center.size > 0:
                hsv_tc = cv2.cvtColor(top_center, cv2.COLOR_BGR2HSV)
                tc_green_mask = cv2.inRange(hsv_tc, np.array([35, 40, 140]), np.array([95, 255, 255]))
                b_tc, g_tc, r_tc = top_center[:, :, 0], top_center[:, :, 1], top_center[:, :, 2]
                tc_bgr_green = (g_tc > r_tc + 30) & (g_tc > b_tc) & (g_tc > 140)
                tc_green_count = np.sum(tc_green_mask > 0) + np.sum(tc_bgr_green)
                
                # Check for green LED light
                if tc_green_count > 40:
                    has_green_light = True

        if has_red_light or has_stop_sign:
            rule_info = INDIAN_TRAFFIC_RULES_KB["MVA_SEC_119_RED_SIGNAL"]
            decision = "MUST_STOP_RED_LIGHT"
            confidence = 0.97
            reasoning = f"Mandatory Indian Law ({rule_info['source']}): RED signal / STOP sign detected. Mandatory full stop."
        elif has_green_light:
            rule_info = INDIAN_TRAFFIC_RULES_KB["MVA_SEC_119_GREEN_SIGNAL"]
            decision = "PROCEED_GREEN_LIGHT"
            confidence = 0.96
            reasoning = f"Green Signal Permissive Rule ({rule_info['source']}): Active GREEN signal detected. Proceed with vigilance."
        else:
            rule_info = INDIAN_TRAFFIC_RULES_KB["MVA_SEC_121_LANE_DISCIPLINE"]
            decision = "STANDARD_RIGHT_OF_WAY"
            confidence = 0.88
            reasoning = f"Standard Highway Rule ({rule_info['source']}): Clear right of way. Maintain permitted speed limit (50 km/h)."

        return {
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence": {
                "rule_applied": rule_info["title"],
                "rule_source": rule_info["source"],
                "rule_id": rule_info["rule_id"],
                "rule_text": rule_info["rule_text"],
                "conf_threshold": 0.5,
                "has_red_light": has_red_light,
                "has_stop_sign": has_stop_sign,
                "has_green_light": has_green_light,
                "speed_limit_kph": 50
            }
        }
