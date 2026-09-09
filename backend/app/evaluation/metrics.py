import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Tuple
from app.config import DATA_DIR
from app.utils.logger import logger

SCORING_CLASSES = ["PROCEED", "SLOW DOWN", "STOP", "EMERGENCY BRAKE"]

def compute_ece(confidences: np.ndarray, correct_mask: np.ndarray, n_bins: int = 10) -> float:
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(confidences)
    if n == 0:
        return 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(correct_mask[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin

    return float(ece)

def bootstrap_ci(arr: np.ndarray, n_boot: int = 1000, ci: float = 0.95, seed: int = 42) -> Tuple[float, float]:
    np.random.seed(seed)
    if len(arr) == 0:
        return 0.0, 0.0
    boot_means = []
    n = len(arr)
    for _ in range(n_boot):
        sample = np.random.choice(arr, size=n, replace=True)
        boot_means.append(np.mean(sample))
    alpha = (1.0 - ci) / 2.0
    low = float(np.percentile(boot_means, alpha * 100))
    high = float(np.percentile(boot_means, (1.0 - alpha) * 100))
    return round(low, 4), round(high, 4)

def mcnemar_test(b_correct: np.ndarray, c_correct: np.ndarray) -> Tuple[float, float]:
    # b_correct: strategy 1, c_correct: strategy 2
    # n01: strat 1 wrong, strat 2 right
    # n10: strat 1 right, strat 2 wrong
    n10 = np.sum(b_correct & ~c_correct)
    n01 = np.sum(~b_correct & c_correct)

    if n10 + n01 == 0:
        return 0.0, 1.0

    # Continuity corrected McNemar statistic
    stat = (abs(n10 - n01) - 1.0)**2 / float(n10 + n01)
    p_val = stats.chi2.sf(stat, 1)
    return float(stat), float(p_val)

def holm_bonferroni(p_values: List[float]) -> List[float]:
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    adjusted_p = np.zeros(n)

    cum_max = 0.0
    for rank, idx in enumerate(sorted_indices):
        p = p_values[idx]
        adj = p * (n - rank)
        adj = min(1.0, max(cum_max, adj))
        cum_max = adj
        adjusted_p[idx] = float(adj)

    return list(adjusted_p)

def calculate_metrics_summary(run_id: str, raw_df: pd.DataFrame = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if raw_df is None:
        raw_path = DATA_DIR / "results" / f"{run_id}_raw.csv"
        if not raw_path.exists():
            raise FileNotFoundError(f"Raw results file not found at {raw_path}")
        raw_df = pd.read_csv(raw_path)

    # 1. Expand Baselines from cached agent_actions
    expanded_rows = []

    # Extract all frame image_paths
    unique_frames = raw_df["image_path"].unique()
    first_strat = raw_df["strategy"].iloc[0]
    frame_subset = raw_df[raw_df["strategy"] == first_strat].copy()

    # Baseline 1: Best Single Agent
    # Collect standalone accuracies of all agents
    agent_names = []
    if len(frame_subset) > 0 and "agent_actions" in frame_subset.columns:
        first_map = json.loads(frame_subset["agent_actions"].iloc[0])
        agent_names = list(first_map.keys())

    agent_correct = {ag: 0 for ag in agent_names}
    total_f = len(frame_subset)

    for _, row in frame_subset.iterrows():
        action_map = json.loads(row["agent_actions"])
        true_act = row["true_action"]
        for ag, act in action_map.items():
            if act == true_act:
                agent_correct[ag] = agent_correct.get(ag, 0) + 1

    best_agent = max(agent_correct, key=agent_correct.get) if agent_correct else "Object Detection Agent"

    for _, row in frame_subset.iterrows():
        action_map = json.loads(row["agent_actions"])
        true_act = row["true_action"]

        # Best Single Agent
        best_act = action_map.get(best_agent, "PROCEED")
        expanded_rows.append({
            "run_id": run_id, "image_path": row["image_path"], "scenario": row["scenario"],
            "strategy": f"Baseline: Best Single Agent ({best_agent})",
            "pred_action": best_act, "true_action": true_act,
            "confidence": 0.85, "was_tie": False, "arbitration_ms": 0.05,
            "perception_ms": row["perception_ms"], "n_conflicts": row["n_conflicts"],
            "max_severity": row["max_severity"], "agreement_rate": row["agreement_rate"],
            "agent_actions": row["agent_actions"]
        })

        # Centralized Planner Baseline
        planner_act = action_map.get("Planning Agent", "PROCEED")
        expanded_rows.append({
            "run_id": run_id, "image_path": row["image_path"], "scenario": row["scenario"],
            "strategy": "Baseline: Centralized Planner",
            "pred_action": planner_act, "true_action": true_act,
            "confidence": 0.90, "was_tie": False, "arbitration_ms": 0.10,
            "perception_ms": row["perception_ms"], "n_conflicts": row["n_conflicts"],
            "max_severity": row["max_severity"], "agreement_rate": row["agreement_rate"],
            "agent_actions": row["agent_actions"]
        })

        # Oracle Upper Bound
        # Correct if ANY agent in voting pool proposed true_action
        voters_actions = [act for name, act in action_map.items() if name != "Planning Agent"]
        oracle_act = true_act if true_act in voters_actions else voters_actions[0]
        expanded_rows.append({
            "run_id": run_id, "image_path": row["image_path"], "scenario": row["scenario"],
            "strategy": "Oracle Upper Bound",
            "pred_action": oracle_act, "true_action": true_act,
            "confidence": 1.0, "was_tie": False, "arbitration_ms": 0.01,
            "perception_ms": row["perception_ms"], "n_conflicts": row["n_conflicts"],
            "max_severity": row["max_severity"], "agreement_rate": row["agreement_rate"],
            "agent_actions": row["agent_actions"]
        })

        # Random Arbitration Baseline (Averaged 5 seeds)
        for seed in range(5):
            np.random.seed(seed + 100)
            rand_act = np.random.choice(voters_actions) if voters_actions else "PROCEED"
            expanded_rows.append({
                "run_id": run_id, "image_path": row["image_path"], "scenario": row["scenario"],
                "strategy": "Baseline: Random Arbitration",
                "pred_action": rand_act, "true_action": true_act,
                "confidence": 0.50, "was_tie": False, "arbitration_ms": 0.02,
                "perception_ms": row["perception_ms"], "n_conflicts": row["n_conflicts"],
                "max_severity": row["max_severity"], "agreement_rate": row["agreement_rate"],
                "agent_actions": row["agent_actions"]
            })

    baseline_df = pd.DataFrame(expanded_rows)
    full_df = pd.concat([raw_df, baseline_df], ignore_index=True)

    # 2. Compute Summary Metrics per Strategy
    summary_rows = []
    strategies = full_df["strategy"].unique()

    for strat in strategies:
        sdf = full_df[full_df["strategy"] == strat].copy()
        n_frames = len(sdf)
        if n_frames == 0:
            continue

        correct_mask = (sdf["pred_action"] == sdf["true_action"]).values
        acc = float(np.mean(correct_mask))

        # Bootstrap CIs
        acc_ci_low, acc_ci_high = bootstrap_ci(correct_mask.astype(float))

        # Missed-stop rate
        stop_mask = sdf["true_action"].isin(["STOP", "EMERGENCY BRAKE"]).values
        missed_stop_arr = (stop_mask & (sdf["pred_action"] == "PROCEED")).values
        missed_stop_rate = float(np.sum(missed_stop_arr) / max(1.0, float(np.sum(stop_mask))))
        ms_ci_low, ms_ci_high = bootstrap_ci(missed_stop_arr.astype(float))

        # False-alarm rate
        proceed_mask = (sdf["true_action"] == "PROCEED").values
        false_alarm_arr = (proceed_mask & sdf["pred_action"].isin(["STOP", "EMERGENCY BRAKE"])).values
        false_alarm_rate = float(np.sum(false_alarm_arr) / max(1.0, float(np.sum(proceed_mask))))

        # Conflict-frame accuracy
        conflict_sdf = sdf[sdf["n_conflicts"] > 0]
        conflict_acc = float(np.mean(conflict_sdf["pred_action"] == conflict_sdf["true_action"])) if len(conflict_sdf) > 0 else acc

        # F1 Scores per class & Macro F1
        f1_scores = []
        for cls_name in SCORING_CLASSES:
            tp = np.sum((sdf["pred_action"] == cls_name) & (sdf["true_action"] == cls_name))
            fp = np.sum((sdf["pred_action"] == cls_name) & (sdf["true_action"] != cls_name))
            fn = np.sum((sdf["pred_action"] != cls_name) & (sdf["true_action"] == cls_name))
            prec = tp / max(1.0, float(tp + fp))
            rec = tp / max(1.0, float(tp + fn))
            f1 = (2 * prec * rec) / max(1e-5, (prec + rec))
            f1_scores.append(f1)

        macro_f1 = float(np.mean(f1_scores))

        # Calibration: Brier score & ECE
        confs = sdf["confidence"].values
        brier = float(np.mean((confs - correct_mask.astype(float)) ** 2))
        ece = compute_ece(confs, correct_mask)

        # Efficiency Latencies
        arb_lat = sdf["arbitration_ms"].values
        mean_arb_lat = float(np.mean(arb_lat))
        std_arb_lat = float(np.std(arb_lat))
        p95_arb_lat = float(np.percentile(arb_lat, 95))

        total_lat = (sdf["perception_ms"] + sdf["arbitration_ms"]).values
        mean_total_lat = float(np.mean(total_lat))
        effective_fps = float(1000.0 / max(0.1, mean_total_lat))

        tie_rate = float(np.mean(sdf["was_tie"].values))
        conf_res_rate = 1.0 - tie_rate

        summary_rows.append({
            "strategy": strat,
            "accuracy": round(acc, 4),
            "acc_ci_low": acc_ci_low,
            "acc_ci_high": acc_ci_high,
            "conflict_frame_acc": round(conflict_acc, 4),
            "missed_stop_rate": round(missed_stop_rate, 4),
            "ms_ci_low": ms_ci_low,
            "ms_ci_high": ms_ci_high,
            "false_alarm_rate": round(false_alarm_rate, 4),
            "macro_f1": round(macro_f1, 4),
            "f1_proceed": round(f1_scores[0], 4),
            "f1_slow_down": round(f1_scores[1], 4),
            "f1_stop": round(f1_scores[2], 4),
            "f1_emergency_brake": round(f1_scores[3], 4),
            "brier_score": round(brier, 4),
            "ece": round(ece, 4),
            "mean_arb_ms": round(mean_arb_lat, 3),
            "std_arb_ms": round(std_arb_lat, 3),
            "p95_arb_ms": round(p95_arb_lat, 3),
            "mean_total_ms": round(mean_total_lat, 2),
            "effective_fps": round(effective_fps, 1),
            "tie_rate": round(tie_rate, 4),
            "conflict_res_rate": round(conf_res_rate, 4),
            "sample_frames": n_frames
        })

    summary_df = pd.DataFrame(summary_rows)
    summary_path = DATA_DIR / "results" / f"{run_id}_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    # 3. Compute Scenario Matrix
    scenario_rows = []
    scenarios = full_df["scenario"].unique()

    for strat in strategies:
        for scen in scenarios:
            scen_df = full_df[(full_df["strategy"] == strat) & (full_df["scenario"] == scen)]
            if len(scen_df) == 0:
                continue

            s_correct = (scen_df["pred_action"] == scen_df["true_action"]).values
            s_acc = float(np.mean(s_correct))

            s_stop = scen_df["true_action"].isin(["STOP", "EMERGENCY BRAKE"]).values
            s_missed = float(np.sum(s_stop & (scen_df["pred_action"] == "PROCEED")) / max(1.0, float(np.sum(s_stop))))

            s_conf_df = scen_df[scen_df["n_conflicts"] > 0]
            s_conf_acc = float(np.mean(s_conf_df["pred_action"] == s_conf_df["true_action"])) if len(s_conf_df) > 0 else s_acc

            scenario_rows.append({
                "strategy": strat,
                "scenario": scen,
                "accuracy": round(s_acc, 4),
                "missed_stop_rate": round(s_missed, 4),
                "conflict_frame_acc": round(s_conf_acc, 4),
                "sample_count": len(scen_df)
            })

    scenario_df = pd.DataFrame(scenario_rows)
    scen_path = DATA_DIR / "results" / f"{run_id}_by_scenario.csv"
    scenario_df.to_csv(scen_path, index=False)

    # 4. Statistical Significance Pairwise Matrix (McNemar + Holm-Bonferroni + Wilcoxon)
    signif_rows = []
    strat_list = [s for s in strategies if not s.startswith("Baseline") and s != "Oracle Upper Bound"]

    p_vals = []
    pair_combos = []

    for i in range(len(strat_list)):
        for j in range(i + 1, len(strat_list)):
            s1 = strat_list[i]
            s2 = strat_list[j]

            df1 = full_df[full_df["strategy"] == s1].sort_values("image_path")
            df2 = full_df[full_df["strategy"] == s2].sort_values("image_path")

            corr1 = (df1["pred_action"] == df1["true_action"]).values
            corr2 = (df2["pred_action"] == df2["true_action"]).values

            stat, p = mcnemar_test(corr1, corr2)

            # Wilcoxon latency test
            lat1 = df1["arbitration_ms"].values
            lat2 = df2["arbitration_ms"].values
            try:
                w_stat, w_p = stats.wilcoxon(lat1, lat2)
            except Exception:
                w_stat, w_p = 0.0, 1.0

            p_vals.append(p)
            pair_combos.append({
                "strategy_A": s1,
                "strategy_B": s2,
                "mcnemar_stat": round(stat, 3),
                "p_value": p,
                "wilcoxon_stat": round(float(w_stat), 3),
                "wilcoxon_p_value": round(float(w_p), 5),
                "acc_A": round(float(np.mean(corr1)), 4),
                "acc_B": round(float(np.mean(corr2)), 4),
                "acc_diff": round(float(np.mean(corr1) - np.mean(corr2)), 4)
            })

    adj_p_vals = holm_bonferroni(p_vals)
    for idx, combo in enumerate(pair_combos):
        combo["adj_p_value"] = round(adj_p_vals[idx], 5)
        combo["is_stat_sig"] = bool(adj_p_vals[idx] < 0.05)
        signif_rows.append(combo)

    signif_df = pd.DataFrame(signif_rows)
    sig_path = DATA_DIR / "results" / f"{run_id}_significance.csv"
    signif_df.to_csv(sig_path, index=False)

    logger.info(f"Saved metric summary, scenario matrix, and statistical significance to {DATA_DIR / 'results'}")
    return summary_df, scenario_df, signif_df

if __name__ == "__main__":
    import sys
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not run_id:
        raw_files = list(glob.glob(str(DATA_DIR / "results" / "*_raw.csv")))
        if raw_files:
            latest_file = max(raw_files, key=os.path.getctime)
            run_id = os.path.basename(latest_file).replace("_raw.csv", "")

    if run_id:
        summary_df, scenario_df, signif_df = calculate_metrics_summary(run_id)
        print("=" * 70)
        print(f"EXPERIMENT METRIC SUMMARY (Run ID: {run_id})")
        print("=" * 70)
        print(summary_df[["strategy", "accuracy", "conflict_frame_acc", "missed_stop_rate", "false_alarm_rate", "mean_arb_ms", "p95_arb_ms", "tie_rate"]].to_string(index=False))
