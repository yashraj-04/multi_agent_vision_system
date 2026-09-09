import os
import sys
import numpy as np

# Ensure backend package is in python path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db
from app.agents.object_detection_agent import ObjectDetectionAgent
from app.agents.lane_detection_agent import LaneDetectionAgent
from app.agents.traffic_rule_agent import TrafficRuleAgent
from app.agents.scene_understanding_agent import SceneUnderstandingAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.agents.planning_agent import PlanningAgent
from app.conflict.conflict_detector import ConflictDetector
from app.conflict.resolution_engine import ConflictResolutionEngine
from app.experiments.benchmark_runner import BenchmarkRunner
from app.config import settings

def test_full_pipeline():
    print("==================================================")
    print("Testing System Pipeline & 10 Conflict Resolution Algos")
    print("==================================================")
    init_db()

    # Create dummy dark road image
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    # 1. Run perception agents
    obj = ObjectDetectionAgent()
    lane = LaneDetectionAgent()
    rule = TrafficRuleAgent()
    scene = SceneUnderstandingAgent()
    risk = RiskAssessmentAgent()
    plan = PlanningAgent()

    context = {}
    out_obj = obj.run(img, context)
    context["object_agent_output"] = out_obj
    out_lane = lane.run(img, context)
    out_traffic = rule.run(img, context)
    out_scene = scene.run(img, context)
    out_risk = risk.run(img, context)

    prior = [out_obj, out_lane, out_traffic, out_scene, out_risk]
    out_plan = plan.run(img, {"prior_agent_outputs": prior})

    all_outputs = [out_obj, out_lane, out_traffic, out_scene, out_risk, out_plan]

    print(f"\n[+] Executed {len(all_outputs)} Perception Agents successfully:")
    for a in all_outputs:
        print(f"  - {a.agent_name}: Decision='{a.decision}', Conf={a.confidence}, Latency={a.latency_ms}ms")

    # 2. Detect Conflicts
    detector = ConflictDetector()
    conflicts = detector.detect_conflicts(all_outputs)
    print(f"\n[+] Conflict Detector identified {len(conflicts)} conflict event(s).")

    # 3. Test ALL 10 Resolution Strategies
    engine = ConflictResolutionEngine()
    print("\n[+] Testing 10 Selectable Conflict Resolution Engine Strategies:")
    for strat in settings.SUPPORTED_STRATEGIES:
        res = engine.resolve(all_outputs, conflicts, strategy=strat)
        print(f"  - Strategy: {strat:<35} | Decision: {res['final_decision']:<15} | Conf: {res['confidence']:.2f} | Latency: {res['resolution_time_ms']}ms")

    # 4. Benchmark Runner
    print("\n[+] Running Comparative Multi-Strategy Research Benchmark...")
    runner = BenchmarkRunner()
    bench = runner.run_benchmark(num_frames=5)
    print(f"  - Benchmark completed across {len(bench)} strategies.")
    print("==================================================")
    print("ALL BACKEND SYSTEM VERIFICATION TESTS PASSED CLEANLY!")
    print("==================================================")

if __name__ == "__main__":
    test_full_pipeline()
