import os
import time
import json
import uuid
import cv2
import pandas as pd
import numpy as np
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
from app.agents.planning_agent import PlanningAgent
from app.agents.strategy_selector_agent import StrategySelectorAgent
from app.conflict.conflict_detector import ConflictDetector, normalize_to_canonical_action
from app.conflict.resolution_engine import ConflictResolutionEngine
from app.conflict.dynamic_reliability import DynamicReliabilityEngine
from app.utils.logger import logger

def to_scoring_space(action: str) -> str:
    if not action:
        return "PROCEED"
    act = str(action).upper()
    if act in ["GO", "TURN LEFT", "TURN RIGHT", "CHANGE LANE", "PROCEED"]:
        return "PROCEED"
    elif act in ["SLOW DOWN", "SLOW", "REDUCE SPEED"]:
        return "SLOW DOWN"
    elif act in ["STOP", "MUST_STOP_RED_LIGHT", "MUST_STOP_SIGN"]:
        return "STOP"
    elif act in ["EMERGENCY BRAKE", "EMERGENCY_BRAKE"]:
        return "EMERGENCY BRAKE"
    return "PROCEED"

def get_max_severity(conflicts: List[Dict[str, Any]]) -> str:
    if not conflicts:
        return "NONE"
    severities = [c.get("severity", "LOW") for c in conflicts]
    if "CRITICAL" in severities:
        return "CRITICAL"
    if "HIGH" in severities:
        return "HIGH"
    if "MEDIUM" in severities:
        return "MEDIUM"
    return "LOW"

def compute_agreement_rate(outputs: List[Any]) -> float:
    actions = []
    for a in outputs:
        dec = getattr(a, "decision", None) or (a.get("decision") if isinstance(a, dict) else "")
        act = normalize_to_canonical_action(dec)
        if act:
            actions.append(to_scoring_space(act))
    if not actions:
        return 1.0
    most_common = max(set(actions), key=actions.count)
    return actions.count(most_common) / float(len(actions))

def get_agent_action_map(outputs: List[Any]) -> Dict[str, str]:
    action_map = {}
    for a in outputs:
        name = getattr(a, "agent_name", None) or (a.get("agent_name") if isinstance(a, dict) else "Agent")
        dec = getattr(a, "decision", None) or (a.get("decision") if isinstance(a, dict) else "")
        act = normalize_to_canonical_action(dec)
        action_map[name] = to_scoring_space(act) if act else "ABSTAIN"
    return action_map

def run_experiment_harness(gt_df: pd.DataFrame = None, limit: int = None, run_id: str = None, seed: int = 42) -> Tuple[str, pd.DataFrame]:
    os.environ["FAST_EVAL"] = "1"
    if gt_df is None or gt_df.empty:
        gt_path = DATA_DIR / "ground_truth.csv"
        if not gt_path.exists():
            from app.evaluation.ground_truth import generate_ground_truth
            gt_df = generate_ground_truth(max_samples=300, seed=seed)
        else:
            gt_df = pd.read_csv(gt_path)

    if limit and len(gt_df) > limit:
        gt_df = gt_df.sample(limit, random_state=seed).reset_index(drop=True)

    run_id = run_id or f"run_{str(uuid.uuid4())[:8]}"
    logger.info(f"Starting Paired Evaluation Harness (Run ID: {run_id}, Samples: {len(gt_df)})...")

    # Initialize perception singletons
    yolo_trainer = YOLOTrainer()
    vision_llm = VisionLLM()
    reliability_engine = DynamicReliabilityEngine()
    conflict_detector = ConflictDetector()
    resolution_engine = ConflictResolutionEngine(reliability_engine)

    # 6 Independent Voting Pool Agents
    voting_agents = [
        ObjectDetectionAgent(yolo_trainer),
        SecondaryObjectDetectionAgent(yolo_trainer),
        LaneDetectionAgent(),
        TrafficRuleAgent(yolo_trainer),
        SceneUnderstandingAgent(vision_llm),
        RiskAssessmentAgent(yolo_trainer)
    ]

    # Baseline & Meta Agents
    planning_agent = PlanningAgent()
    strategy_selector_agent = StrategySelectorAgent()

    # Pre-Calibrate Agent Reliability Scores on Ground Truth
    agent_correct_counts = {a.name: 0 for a in voting_agents}
    total_eval_frames = len(gt_df)

    # All 10 strategies + Adaptive Strategy Selection
    strategies_to_evaluate = list(ALL_STRATEGIES) + ["Adaptive Strategy Selection"]

    results_rows = []

    for idx, row in gt_df.iterrows():
        img_path = row["image_path"]
        true_action = row["true_action"]
        scenario_tag = row["scenario_tag"]

        img = cv2.imread(img_path)
        if img is None:
            continue

        # 1. Run perception ONCE per frame & cache outputs
        t_perc_start = time.perf_counter()
        outputs = []
        context = {}
        for agent in voting_agents:
            out = agent.run(img, context)
            outputs.append(out)
            # Track calibration
            dec = getattr(out, "decision", "")
            act = to_scoring_space(normalize_to_canonical_action(dec))
            if act == true_action:
                agent_correct_counts[agent.name] += 1

        perception_ms = (time.perf_counter() - t_perc_start) * 1000.0

        # Run Planning Agent Baseline separately
        planner_out = planning_agent.run(img, {"prior_agent_outputs": outputs})

        # Detect conflicts
        conflicts = conflict_detector.detect_conflicts(outputs)
        max_sev = get_max_severity(conflicts)
        agreement = compute_agreement_rate(outputs)
        action_map = get_agent_action_map(outputs)
        action_map["Planning Agent"] = to_scoring_space(normalize_to_canonical_action(planner_out.decision))

        # Run Strategy Selector Meta-Agent
        meta_out = strategy_selector_agent.run(img, {"prior_agent_outputs": outputs, "conflicts": conflicts})
        auto_strat = meta_out.decision

        # 2. Evaluate every strategy on the IDENTICAL cached outputs
        for strat in strategies_to_evaluate:
            actual_strat = auto_strat if strat == "Adaptive Strategy Selection" else strat
            t0 = time.perf_counter()
            r = resolution_engine.resolve(outputs, conflicts, strategy=actual_strat)
            arb_ms = (time.perf_counter() - t0) * 1000.0

            pred_action = to_scoring_space(r["final_decision"])

            results_rows.append({
                "run_id": run_id,
                "image_path": img_path,
                "scenario": scenario_tag,
                "strategy": strat,
                "auto_selected_strategy": auto_strat if strat == "Adaptive Strategy Selection" else "",
                "pred_action": pred_action,
                "true_action": true_action,
                "confidence": r["confidence"],
                "was_tie": r.get("was_tie", False),
                "arbitration_ms": arb_ms,
                "perception_ms": perception_ms,
                "n_conflicts": len(conflicts),
                "max_severity": max_sev,
                "agreement_rate": agreement,
                "agent_actions": json.dumps(action_map)
            })

        if (idx + 1) % 25 == 0 or (idx + 1) == len(gt_df):
            logger.info(f"Processed {idx + 1}/{len(gt_df)} frames across {len(strategies_to_evaluate)} strategies.")

    # Calibrate starting reliability from actual per-agent accuracies
    calibrated_accuracies = {name: cnt / max(1.0, float(total_eval_frames)) for name, cnt in agent_correct_counts.items()}
    reliability_engine.calibrate_from_ground_truth(calibrated_accuracies)

    results_df = pd.DataFrame(results_rows)
    os.makedirs(str(DATA_DIR / "results"), exist_ok=True)
    raw_path = DATA_DIR / "results" / f"{run_id}_raw.csv"
    results_df.to_csv(raw_path, index=False)
    logger.info(f"Saved raw harness experiment results ({len(results_df)} rows) to {raw_path}")

    return run_id, results_df

if __name__ == "__main__":
    run_id, df = run_experiment_harness()
    print("=" * 60)
    print(f"EXPERIMENT HARNESS RUN COMPLETE (Run ID: {run_id})")
    print("=" * 60)
    print(f"Total Rows Evaluated: {len(df)}")
    print("Strategies Tested:")
    print(df["strategy"].value_counts())
