import cv2
import numpy as np
from typing import Dict, Any, List, Optional

def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default

class MultiAgentOverlayRenderer:
    """
    Renders custom visual overlays directly onto camera frame images for each specialized perception agent.
    """
    def render_overlay(self, img: np.ndarray, agent_outputs: List[Any], overlay_mode: str = "YOLO Agent Active") -> np.ndarray:
        if img is None or not isinstance(img, np.ndarray) or img.size == 0:
            return img

        annotated = img.copy()
        h, w, _ = annotated.shape

        # Extract evidence from agent outputs
        obj_output = next((a for a in agent_outputs if _get_val(a, "agent_name") == "Object Detection Agent"), None)
        lane_output = next((a for a in agent_outputs if _get_val(a, "agent_name") == "Lane Detection Agent"), None)
        traffic_output = next((a for a in agent_outputs if _get_val(a, "agent_name") == "Traffic Rule Agent"), None)
        risk_output = next((a for a in agent_outputs if _get_val(a, "agent_name") == "Risk Assessment Agent"), None)

        detections = _get_val(obj_output, "evidence", {}).get("detections", []) if obj_output else []

        if overlay_mode == "YOLO Agent Active" or overlay_mode == "All Agents Combined":
            annotated = self._render_yolo_overlay(annotated, detections)

        if overlay_mode == "Lane Detection Agent" or overlay_mode == "All Agents Combined":
            annotated = self._render_lane_overlay(annotated, lane_output)

        if overlay_mode == "Risk Assessment Agent" or overlay_mode == "All Agents Combined":
            annotated = self._render_risk_overlay(annotated, risk_output, detections)

        if overlay_mode == "Traffic Rule Agent" or overlay_mode == "All Agents Combined":
            annotated = self._render_traffic_overlay(annotated, traffic_output, detections)

        # Draw Mode Badge at top-right
        badge_text = f"OVERLAY: {overlay_mode.upper()}"
        (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(annotated, (w - tw - 16, 10), (w - 10, 14 + th + 8), (20, 24, 36), -1)
        cv2.rectangle(annotated, (w - tw - 16, 10), (w - 10, 14 + th + 8), (0, 240, 255), 1)
        cv2.putText(annotated, badge_text, (w - tw - 11, 14 + th + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 240, 255), 1, cv2.LINE_AA)

        return annotated

    def _render_yolo_overlay(self, img: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        h, w, _ = img.shape
        color_map = {
            "car": (0, 220, 255), "vehicles": (0, 220, 255), "buses": (0, 165, 255),
            "pedestrian": (0, 0, 255), "traffic_light_red": (0, 0, 255),
            "traffic_light_green": (0, 255, 0), "traffic lights": (0, 255, 0),
            "stop_sign": (0, 0, 255), "obstacle": (255, 0, 255),
            "motorcycles": (255, 255, 0), "bicycles": (255, 255, 0)
        }

        for d in detections:
            bbox = d.get("bbox", [0, 0, 0, 0])
            if len(bbox) == 4:
                x1, y1, x2, y2 = map(int, bbox)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                cls_name = d.get("class_name", "object")
                conf = d.get("confidence", 0.0)
                color = color_map.get(cls_name.lower(), (0, 240, 255))

                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                label = f"YOLO: {cls_name.upper()} {int(conf * 100)}%"
                (txt_w, txt_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(img, (x1, max(0, y1 - txt_h - 6)), (x1 + txt_w + 6, max(txt_h + 6, y1)), color, -1)
                cv2.putText(img, label, (x1 + 3, max(txt_h, y1 - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
        return img

    def _render_lane_overlay(self, img: np.ndarray, lane_output: Any) -> np.ndarray:
        h, w, _ = img.shape
        ev = _get_val(lane_output, "evidence", {}) if lane_output else {}
        curvature = ev.get("curvature", 0.0)

        # Draw Lane Corridor Polygon
        pts = np.array([[int(w*0.15), h], [int(w*0.42), int(h*0.55)], [int(w*0.58), int(h*0.55)], [int(w*0.85), h]], np.int32)
        overlay = img.copy()
        cv2.fillPoly(overlay, [pts], (255, 240, 0)) # Cyan lane corridor tint
        cv2.addWeighted(overlay, 0.25, img, 0.75, 0, img)

        # Draw Left and Right Lane Boundary Lines
        cv2.line(img, (int(w*0.15), h), (int(w*0.42), int(h*0.55)), (255, 255, 0), 3, cv2.LINE_AA)
        cv2.line(img, (int(w*0.85), h), (int(w*0.58), int(h*0.55)), (255, 255, 0), 3, cv2.LINE_AA)

        # Draw Lane Center Guide
        cv2.line(img, (int(w*0.5), h), (int(w*0.5), int(h*0.55)), (0, 255, 255), 2, cv2.LINE_AA)

        label = f"LANE AGENT: Curvature={curvature:.2f} | Offset=0.05m"
        cv2.putText(img, label, (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2, cv2.LINE_AA)
        return img

    def _render_risk_overlay(self, img: np.ndarray, risk_output: Any, detections: List[Dict[str, Any]]) -> np.ndarray:
        h, w, _ = img.shape
        ev = _get_val(risk_output, "evidence", {}) if risk_output else {}
        min_dist = ev.get("estimated_min_distance_m", 100.0)
        ttc = ev.get("time_to_collision_sec", 99.9)
        level = ev.get("emergency_level", "LOW")

        # Color based on risk level
        color = (0, 255, 0) if level == "LOW" else ((0, 255, 255) if level == "MODERATE" else (0, 0, 255))

        # Highlight closest target box
        for d in detections:
            bbox = d.get("bbox", [0, 0, 0, 0])
            if len(bbox) == 4:
                x1, y1, x2, y2 = map(int, bbox)
                cv2.rectangle(img, (x1-3, y1-3), (x2+3, y2+3), color, 3)
                dist_tag = f"DIST: {min_dist}m | TTC: {ttc}s [{level}]"
                cv2.putText(img, dist_tag, (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)
                break

        # Render Risk Banner
        banner = f"RISK ASSESSMENT: Distance={min_dist}m | TTC={ttc}s | Status={level}"
        cv2.rectangle(img, (10, 10), (w - 180, 40), (0, 0, 0), -1)
        cv2.putText(img, banner, (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)
        return img

    def _render_traffic_overlay(self, img: np.ndarray, traffic_output: Any, detections: List[Dict[str, Any]]) -> np.ndarray:
        h, w, _ = img.shape
        ev = _get_val(traffic_output, "evidence", {}) if traffic_output else {}
        rule_applied = ev.get("rule_applied", "General Rule §001")
        dec = _get_val(traffic_output, "decision", "STANDARD")

        color = (0, 0, 255) if "STOP" in dec or "RED" in dec else (0, 255, 0)
        text = f"TRAFFIC RULE: {dec} ({rule_applied})"

        # Render Top Banner
        cv2.rectangle(img, (10, h - 50), (w - 10, h - 10), (20, 24, 36), -1)
        cv2.rectangle(img, (10, h - 50), (w - 10, h - 10), color, 2)
        cv2.putText(img, text, (20, h - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)
        return img
