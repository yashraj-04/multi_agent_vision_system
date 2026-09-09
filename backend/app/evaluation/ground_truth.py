import os
import cv2
import yaml
import glob
import random
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from app.config import DATASET_DIR, DATA_DIR
from app.utils.logger import logger

VULNERABLE_NAMES = {"bicycles", "motorcycles", "pedestrian", "person"}
VEHICLE_NAMES = {"vehicles", "buses", "taxis", "tractors", "car"}
SIGNAL_NAMES = {"traffic lights", "traffic_light", "traffic_light_red", "traffic_light_green", "stop_sign"}
CROSSING_NAMES = {"crosswalks"}

def get_dataset_class_names() -> List[str]:
    yaml_path = DATASET_DIR / "data.yaml"
    if not yaml_path.exists():
        yaml_path = DATASET_DIR / "dataset.yaml"
    
    if yaml_path.exists():
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f)
                names = data.get("names", [])
                if isinstance(names, dict):
                    return [names[i] for i in sorted(names.keys())]
                elif isinstance(names, list):
                    return names
        except Exception as e:
            logger.warning(f"Error reading dataset YAML: {e}")
            
    return ['bicycles', 'bridges', 'buses', 'chimneys', 'crosswalks', 'fire hydrants', 'motorcycles', 'stairs', 'taxis', 'tractors', 'traffic lights', 'vehicles']

def calculate_iou(boxA, boxB):
    # box format: [x1, y1, x2, y2]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)
    return iou

def compute_scenario_tag(img_path: str, boxes: List[Dict[str, Any]]) -> str:
    img = cv2.imread(img_path)
    if img is None:
        return "clear_day"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    if mean_val < 70:
        return "night_low_light"
    if laplacian_var < 100:
        return "blurred"
    if len(boxes) >= 5:
        return "high_density"

    # Check for occlusion (IoU > 0.3)
    coords = []
    for b in boxes:
        xc, yc, w, h = b["xc"], b["yc"], b["w"], b["h"]
        coords.append([xc - w/2, yc - h/2, xc + w/2, yc + h/2])

    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            if calculate_iou(coords[i], coords[j]) > 0.3:
                return "occluded"

    return "clear_day"

def is_red_light_crop(img: np.ndarray, xc: float, yc: float, w: float, h: float) -> bool:
    ih, iw, _ = img.shape
    x1, y1 = max(0, int((xc - w/2) * iw)), max(0, int((yc - h/2) * ih))
    x2, y2 = min(iw, int((xc + w/2) * iw)), min(ih, int((yc + h/2) * ih))
    if x2 <= x1 or y2 <= y1:
        return False
    crop = img[y1:y2, x1:x2]
    if crop.size == 0:
        return False
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
    mask2 = cv2.inRange(hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
    red_count = np.sum((mask1 | mask2) > 0)
    return (red_count / float(crop.shape[0] * crop.shape[1])) > 0.08

def derive_true_action(img_path: str, boxes: List[Dict[str, Any]]) -> str:
    img = cv2.imread(img_path)
    
    # Rule 1: Vulnerable class height > 0.25 in middle third
    for b in boxes:
        if b["name"] in VULNERABLE_NAMES and b["h"] > 0.25 and (0.33 <= b["xc"] <= 0.67):
            return "EMERGENCY BRAKE"

    # Rule 2: Vehicle class height > 0.35 in middle third
    for b in boxes:
        if b["name"] in VEHICLE_NAMES and b["h"] > 0.35 and (0.33 <= b["xc"] <= 0.67):
            return "EMERGENCY BRAKE"

    # Rule 3: Signal class in top 40% red-dominant
    for b in boxes:
        if b["name"] in SIGNAL_NAMES and b["yc"] < 0.4:
            if img is not None and is_red_light_crop(img, b["xc"], b["yc"], b["w"], b["h"]):
                return "STOP"

    # Rule 4: Vulnerable class present anywhere OR crossing present
    for b in boxes:
        if b["name"] in VULNERABLE_NAMES or b["name"] in CROSSING_NAMES:
            return "SLOW DOWN"

    # Rule 5: Vehicle class height > 0.15 in middle third
    for b in boxes:
        if b["name"] in VEHICLE_NAMES and b["h"] > 0.15 and (0.33 <= b["xc"] <= 0.67):
            return "SLOW DOWN"

    # Rule 6: Default PROCEED
    return "PROCEED"

def generate_ground_truth(max_samples: int = 300, seed: int = 42) -> pd.DataFrame:
    class_names = get_dataset_class_names()
    logger.info(f"Loaded {len(class_names)} dataset classes: {class_names}")

    # Gather all image files
    img_files = []
    for split in ["valid", "train", "test", "images"]:
        search_path = str(DATASET_DIR / split / "**" / "*.jpg")
        img_files.extend(glob.glob(search_path, recursive=True))
        search_png = str(DATASET_DIR / split / "**" / "*.png")
        img_files.extend(glob.glob(search_png, recursive=True))

    img_files = sorted(list(set(img_files)))
    if not img_files:
        raise FileNotFoundError(f"No image files found under {DATASET_DIR}")

    random.seed(seed)
    if len(img_files) > max_samples:
        selected_imgs = random.sample(img_files, max_samples)
    else:
        selected_imgs = img_files

    rows = []
    for img_path in selected_imgs:
        # Find corresponding label file
        label_path = img_path.replace("\\images\\", "\\labels\\").replace("/images/", "/labels/")
        label_path = os.path.splitext(label_path)[0] + ".txt"

        boxes = []
        if os.path.exists(label_path):
            with open(label_path, 'r') as lf:
                for line in lf:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_idx = int(parts[0])
                        cls_name = class_names[cls_idx] if cls_idx < len(class_names) else f"class_{cls_idx}"
                        xc, yc, w, h = map(float, parts[1:5])
                        boxes.append({"cls_idx": cls_idx, "name": cls_name, "xc": xc, "yc": yc, "w": w, "h": h})

        scenario_tag = compute_scenario_tag(img_path, boxes)
        true_action = derive_true_action(img_path, boxes)
        source = "rule_derived"

        rows.append({
            "image_path": img_path,
            "true_action": true_action,
            "scenario_tag": scenario_tag,
            "source": source
        })

    df = pd.DataFrame(rows)

    # Check for manual overrides
    override_path = DATA_DIR / "ground_truth_overrides.csv"
    if override_path.exists():
        try:
            overrides = pd.read_csv(override_path)
            for idx, o_row in overrides.iterrows():
                match_mask = df["image_path"] == o_row["image_path"]
                if match_mask.any():
                    df.loc[match_mask, "true_action"] = o_row["true_action"]
                    df.loc[match_mask, "source"] = "manual"
            logger.info("Applied ground_truth_overrides.csv successfully.")
        except Exception as e:
            logger.warning(f"Error loading overrides: {e}")

    out_csv = DATA_DIR / "ground_truth.csv"
    df.to_csv(out_csv, index=False)
    logger.info(f"Saved ground truth dataset ({len(df)} rows) to {out_csv}")
    return df

if __name__ == "__main__":
    df = generate_ground_truth(max_samples=300, seed=42)
    print("=" * 60)
    print("GROUND TRUTH DATASET SUMMARY")
    print("=" * 60)
    print(f"Total Rows: {len(df)}")
    print("Class Distribution:")
    print(df["true_action"].value_counts())
    print("\nScenario Tag Distribution:")
    print(df["scenario_tag"].value_counts())
    print("\n30 Random Sample Rows:")
    sample = df.sample(min(30, len(df)), random_state=42)
    for idx, r in sample.iterrows():
        print(f"[{r['source']}] {os.path.basename(r['image_path'])} -> {r['true_action']} ({r['scenario_tag']})")
