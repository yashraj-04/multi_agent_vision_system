import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from app.database import get_db_connection
from app.utils.logger import logger

RESTRICTIVE_ACTIONS = {"STOP", "EMERGENCY BRAKE", "SLOW DOWN"}
STOP_ACTIONS = {"STOP", "EMERGENCY BRAKE"}

class DynamicReliabilityEngine:
    """
    Tracks and updates historical reliability scores for each perception agent in memory.
    Evaluates FP (restrictive action proposed when true was PROCEED) and FN (PROCEED proposed when true was STOP/EMERGENCY BRAKE),
    incorporating a Brier-score confidence calibration penalty.
    """
    def __init__(self):
        self.scores: Dict[str, float] = {}
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self._load_scores()

    def _load_scores(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_reliability")
            rows = cursor.fetchall()
            for r in rows:
                name = r["agent_name"]
                self.scores[name] = float(r["reliability_score"])
                self.metrics[name] = dict(r)
            conn.close()
        except Exception as e:
            logger.warning(f"Failed to load reliability scores from DB: {e}")

    def get_score(self, agent_name: str) -> float:
        return self.scores.get(agent_name, 0.85)

    def update_agent_feedback(self, agent_name: str, proposed_action: str, true_action: str, confidence: float, latency_ms: float, is_conflict: bool):
        if not true_action or proposed_action is None:
            return

        was_correct = (proposed_action == true_action)
        is_fp = (proposed_action in RESTRICTIVE_ACTIONS and true_action == "PROCEED")
        is_fn = (proposed_action == "PROCEED" and true_action in STOP_ACTIONS)

        m = self.metrics.get(agent_name, {
            "agent_name": agent_name,
            "reliability_score": 0.85,
            "total_decisions": 0,
            "successful_decisions": 0,
            "failed_decisions": 0,
            "conflict_count": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "avg_confidence": 0.8,
            "avg_latency_ms": 10.0,
            "brier_score_sum": 0.0
        })

        total = m["total_decisions"] + 1
        success = m["successful_decisions"] + (1 if was_correct else 0)
        failed = m["failed_decisions"] + (0 if was_correct else 1)
        conflicts = m["conflict_count"] + (1 if is_conflict else 0)
        fp = m["false_positives"] + (1 if is_fp else 0)
        fn = m["false_negatives"] + (1 if is_fn else 0)

        # Brier Score penalty: (confidence - is_correct)^2
        target_val = 1.0 if was_correct else 0.0
        brier = (confidence - target_val) ** 2
        brier_sum = m.get("brier_score_sum", 0.0) + brier

        alpha = 0.1
        avg_conf = (1 - alpha) * m.get("avg_confidence", 0.8) + alpha * confidence
        avg_lat = (1 - alpha) * m.get("avg_latency_ms", 10.0) + alpha * latency_ms

        acc = success / max(total, 1)
        fp_rate = fp / max(total, 1)
        fn_rate = fn / max(total, 1)
        mean_brier = brier_sum / max(total, 1)
        calibration_factor = max(0.5, 1.0 - (0.2 * mean_brier))

        new_score = round(min(1.0, max(0.1, (acc * (1.0 - 0.2 * fp_rate - 0.4 * fn_rate)) * calibration_factor)), 3)

        m.update({
            "reliability_score": new_score,
            "total_decisions": total,
            "successful_decisions": success,
            "failed_decisions": failed,
            "conflict_count": conflicts,
            "false_positives": fp,
            "false_negatives": fn,
            "avg_confidence": avg_conf,
            "avg_latency_ms": avg_lat,
            "brier_score_sum": brier_sum
        })

        self.metrics[agent_name] = m
        self.scores[agent_name] = new_score

    def flush_to_db(self):
        """Batched write of in-memory metrics to database."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            for agent_name, m in self.metrics.items():
                cursor.execute("""
                INSERT OR REPLACE INTO agent_reliability (
                    agent_name, reliability_score, total_decisions, successful_decisions,
                    failed_decisions, conflict_count, false_positives, false_negatives,
                    avg_confidence, avg_latency_ms, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    agent_name, m["reliability_score"], m["total_decisions"], m["successful_decisions"],
                    m["failed_decisions"], m["conflict_count"], m["false_positives"], m["false_negatives"],
                    m["avg_confidence"], m["avg_latency_ms"], datetime.now().isoformat()
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to flush reliability metrics to DB: {e}")

    def get_all_reliability_metrics(self) -> Dict[str, Any]:
        """Returns map of agent reliability metrics."""
        return self.metrics if self.metrics else {
            agent: {"agent_name": agent, "reliability_score": score, "total_decisions": 10, "successful_decisions": 9}
            for agent, score in self.scores.items()
        }

    def calibrate_from_ground_truth(self, agent_accuracies: Dict[str, float]):
        """Seeds starting reliability scores from ground-truth evaluation split."""
        for agent_name, acc in agent_accuracies.items():
            score = round(min(1.0, max(0.1, acc)), 3)
            self.scores[agent_name] = score
            if agent_name in self.metrics:
                self.metrics[agent_name]["reliability_score"] = score
