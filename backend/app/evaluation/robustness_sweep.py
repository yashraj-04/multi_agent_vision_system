import os
import cv2
import time
import json
import uuid
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from app.config import ALL_STRATEGIES, DATA_DIR
from app.yolo_trainer import YOLOTrainer
from app.vision_llm import VisionLLM
from app.agents.object_detection_agent import ObjectDetectionAgent
from app.agents.secondary_object_agent import SecondaryObjectDetectionAgent
from app.agents.lane_detection_agent import LaneDetectionAgent
from app.agents.traffic_rule_agent import TrafficRuleAgent
from app.agents.scene_understanding_agent import SceneUnderstandingAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.conflict.conflict_detector import ConflictDetector, normalize_to_canonical_action
from app.conflict.resolution_engine import ConflictResolutionEngine
from app.conflict.dynamic_reliability import DynamicReliabilityEngine
from app.evaluation.harness import to_scoring_space, get_max_severity, compute_agreement_rate, get_agent_action_map
from app.utils.logger import logger

def apply_gaussian_noise(img: np.ndarray, sigma: float) -> np.ndarray:
    noisy = img.astype(np.float32) + np.random.normal(0, sigma, img.shape)
    return np.clip(noisy, 0, 255).astype(np.uint8)

def apply_motion_blur(img: np.ndarray, kernel_size: int) -> np.ndarray:
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[int((kernel_size-1)/2), :] = 1.0 / kernel_size
    return cv2.filter2D(img, -1, kernel)

def apply_brightness_drop(img: np.ndarray, factor: float) -> np.ndarray:
    return np.clip(img.astype(np.float32) * factor, 0, 255).astype(np.uint8)

def apply_occlusion(img: np.ndarray, coverage_pct: float) -> np.ndarray:
    h, w, _ = img.shape
    patch_h = int(h * np.sqrt(coverage_pct))
    patch_w = int(w * np.sqrt(coverage_pct))
    top = int((h - patch_h) / 2)
    left = int((w - patch_w) / 2)
    corrupted = img.copy()
    corrupted[top:top+patch_h, left:left+patch_w] = 0
    return corrupted

PERTURBATION_SPECS = [
    {"type": "clean", "severity": "none", "func": lambda img: img},
    {"type": "gaussian_noise", "severity": "low", "func": lambda img: apply_gaussian_noise(img, 10.0)},
    {"type": "gaussian_noise", "severity": "medium", "func": lambda img: apply_gaussian_noise(img, 25.0)},
    {"type": "gaussian_noise", "severity": "severe", "func": lambda img: apply_gaussian_noise(img, 50.0)},
    {"type": "motion_blur", "severity": "low", "func": lambda img: apply_motion_blur(img, 5)},
    {"type": "motion_blur", "severity": "medium", "func": lambda img: apply_motion_blur(img, 11)},
    {"type": "motion_blur", "severity": "severe", "func": lambda img: apply_motion_blur(img, 21)},
    {"type": "brightness_drop", "severity": "low", "func": lambda img: apply_brightness_drop(img, 0.7)},
    {"type": "brightness_drop", "severity": "medium", "func": lambda img: apply_brightness_drop(img, 0.5)},
    {"type": "brightness_drop", "severity": "severe", "func": lambda img: apply_brightness_drop(img, 0.3)},
    {"type": "occlusion", "severity": "low", "func": lambda img: apply_occlusion(img, 0.10)},
    {"type": "occlusion", "severity": "medium", "func": lambda img: apply_occlusion(img, 0.25)},
    {"type": "occlusion", "severity": "severe", "func": lambda img: apply_occlusion(img, 0.40)}
]

def run_robustness_sweep(gt_df: pd.DataFrame = None, limit: int = 50, run_id: str = None) -> Tuple[str, pd.DataFrame]:
    os.environ["FAST_EVAL"] = "1"
    if gt_df is None or gt_df.empty:
        gt_path = DATA_DIR / "ground_truth.csv"
        if not gt_path.exists():
            from app.evaluation.ground_truth import generate_ground_truth
            gt_df = generate_ground_truth(max_samples=300, seed=42)
        else:
            gt_df = pd.read_csv(gt_path)

    if limit and len(gt_df) > limit:
        gt_df = gt_df.sample(limit, random_state=42).reset_index(drop=True)

    run_id = run_id or f"sweep_{str(uuid.uuid4())[:8]}"
    logger.info(f"Starting Controlled Robustness Sweep (Run ID: {run_id}, Samples: {len(gt_df)}, Perturbations: {len(PERTURBATION_SPECS)})...")

    # Perception Agents & Engines
    yolo_trainer = YOLOTrainer()
    vision_llm = VisionLLM()
    reliability_engine = DynamicReliabilityEngine()
    conflict_detector = ConflictDetector()
    resolution_engine = ConflictResolutionEngine(reliability_engine)

    voting_agents = [
        ObjectDetectionAgent(yolo_trainer),
        SecondaryObjectDetectionAgent(yolo_trainer),
        LaneDetectionAgent(),
        TrafficRuleAgent(yolo_trainer),
        SceneUnderstandingAgent(vision_llm),
        RiskAssessmentAgent(yolo_trainer)
    ]

    strategies = list(ALL_STRATEGIES) + ["Adaptive Strategy Selection"]
    rows = []

    for idx, row in gt_df.iterrows():
        img_path = row["image_path"]
        true_action = row["true_action"]
        raw_img = cv2.imread(img_path)
        if raw_img is None:
            continue

        for p_spec in PERTURBATION_SPECS:
            p_type = p_spec["type"]
            p_sev = p_spec["severity"]
            corrupted_img = p_spec["func"](raw_img)

            t_perc_start = time.perf_counter()
            outputs = []
            context = {}
            for agent in voting_agents:
                out = agent.run(corrupted_img, context)
                outputs.append(out)
            perception_ms = (time.perf_counter() - t_perc_start) * 1000.0

            conflicts = conflict_detector.detect_conflicts(outputs)
            max_sev = get_max_severity(conflicts)
            agreement = compute_agreement_rate(outputs)

            for strat in strategies:
                t0 = time.perf_counter()
                r = resolution_engine.resolve(outputs, conflicts, strategy=strat)
                arb_ms = (time.perf_counter() - t0) * 1000.0
                pred_action = to_scoring_space(r["final_decision"])

                rows.append({
                    "run_id": run_id,
                    "image_path": img_path,
                    "perturbation_type": p_type,
                    "severity": p_sev,
                    "strategy": strat,
                    "pred_action": pred_action,
                    "true_action": true_action,
                    "is_correct": bool(pred_action == true_action),
                    "confidence": r["confidence"],
                    "was_tie": r.get("was_tie", False),
                    "arbitration_ms": arb_ms,
                    "perception_ms": perception_ms,
                    "n_conflicts": len(conflicts),
                    "agreement_rate": agreement
                })

        if (idx + 1) % 10 == 0 or (idx + 1) == len(gt_df):
            logger.info(f"Robustness Sweep: Processed {idx + 1}/{len(gt_df)} images across all perturbations.")

    sweep_df = pd.DataFrame(rows)
    os.makedirs(str(DATA_DIR / "results"), exist_ok=True)
    sweep_path = DATA_DIR / "results" / f"{run_id}_robustness.csv"
    sweep_df.to_csv(sweep_path, index=False)
    logger.info(f"Saved Robustness Sweep results ({len(sweep_df)} rows) to {sweep_path}")

    return run_id, sweep_df

if __name__ == "__main__":
    run_id, df = run_robustness_sweep(limit=30)
    print("=" * 60)
    print(f"ROBUSTNESS SWEEP COMPLETE (Run ID: {run_id})")
    print("=" * 60)
    print(f"Total Perturbed Frames Evaluated: {len(df)}")
    print("\nAccuracy by Perturbation Type & Severity:")
    summary = df.groupby(["perturbation_type", "severity", "strategy"])["is_correct"].mean().unstack("strategy")
    print(summary.round(3))
