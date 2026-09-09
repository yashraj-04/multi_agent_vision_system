import io
import base64
import cv2
import json
import numpy as np
from PIL import Image
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from app.config import settings, SAMPLE_IMAGES_DIR, DB_PATH, DATA_DIR
from app.database import init_db, get_db_connection, save_prediction_and_conflicts, log_event
from app.vision_llm import VisionLLM
from app.dataset_manager import DatasetManager
from app.yolo_trainer import YOLOTrainer

from app.agents.object_detection_agent import ObjectDetectionAgent
from app.agents.lane_detection_agent import LaneDetectionAgent
from app.agents.traffic_rule_agent import TrafficRuleAgent
from app.agents.scene_understanding_agent import SceneUnderstandingAgent
from app.agents.risk_assessment_agent import RiskAssessmentAgent
from app.agents.planning_agent import PlanningAgent

from app.conflict.conflict_detector import ConflictDetector
from app.conflict.resolution_engine import ConflictResolutionEngine
from app.conflict.dynamic_reliability import DynamicReliabilityEngine
from app.memory.agent_memory import AgentMemory
from app.experiments.benchmark_runner import BenchmarkRunner
from app.utils.visualization import AnalyticsVisualizer
from app.utils.logger import logger

# Initialize DB
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Research-Grade Autonomous Driving Multi-Agent Perception & Conflict Resolution System",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
dataset_mgr = DatasetManager()
yolo_trainer = YOLOTrainer()
vision_llm = VisionLLM()
reliability_engine = DynamicReliabilityEngine()
conflict_detector = ConflictDetector()
resolution_engine = ConflictResolutionEngine(reliability_engine)
agent_memory = AgentMemory()
benchmark_runner = BenchmarkRunner()
visualizer = AnalyticsVisualizer()

from app.agents.secondary_object_agent import SecondaryObjectDetectionAgent
from app.agents.strategy_selector_agent import StrategySelectorAgent

# Instantiate Perception Agents
object_agent = ObjectDetectionAgent(yolo_trainer)
secondary_agent = SecondaryObjectDetectionAgent(yolo_trainer)
lane_agent = LaneDetectionAgent()
traffic_agent = TrafficRuleAgent(yolo_trainer)
scene_agent = SceneUnderstandingAgent(vision_llm)
risk_agent = RiskAssessmentAgent(yolo_trainer)
planning_agent = PlanningAgent()
strategy_selector_agent = StrategySelectorAgent()

# Ensure synthetic dataset exists out-of-the-box
dataset_mgr.generate_synthetic_dataset(num_samples=15)

class ConfigUpdateSchema(BaseModel):
    vision_model: Optional[str] = None
    default_strategy: Optional[str] = None

class ConflictResolveRequestSchema(BaseModel):
    strategy: str = "Hybrid Arbitration"
    agent_outputs: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]

@app.on_event("startup")
def startup_event():
    log_event("INFO", "/startup", "FastAPI Server launched successfully.")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "vision_model": vision_llm.model_name,
        "active_strategy": settings.DEFAULT_STRATEGY,
        "supported_models": settings.SUPPORTED_VISION_MODELS,
        "supported_strategies": settings.SUPPORTED_STRATEGIES
    }

@app.get("/config")
def get_config():
    return {
        "vision_model": vision_llm.model_name,
        "supported_models": settings.SUPPORTED_VISION_MODELS,
        "active_strategy": settings.DEFAULT_STRATEGY,
        "supported_strategies": settings.SUPPORTED_STRATEGIES,
        "ollama_host": settings.OLLAMA_HOST
    }

@app.post("/config")
def update_config(payload: ConfigUpdateSchema):
    if payload.vision_model:
        vision_llm.model_name = payload.vision_model
        scene_agent.vision_llm.model_name = payload.vision_model
    if payload.default_strategy:
        settings.DEFAULT_STRATEGY = payload.default_strategy
    log_event("INFO", "/config", f"Updated config: Model={vision_llm.model_name}, Strategy={settings.DEFAULT_STRATEGY}")
    return {"status": "updated", "vision_model": vision_llm.model_name, "active_strategy": settings.DEFAULT_STRATEGY}

@app.post("/train")
def train_yolo(epochs: int = 3):
    import json as _json
    log_event("INFO", "/train", f"Triggered YOLO training for {epochs} epochs.")
    res = yolo_trainer.train(epochs=epochs)
    # Persist results so /get_metrics can serve them even after server restart
    if res.get("status") == "success":
        training_results_file = DATA_DIR / "training_results.json"
        dataset_stats = dataset_mgr.generate_statistics()
        res["dataset_statistics"] = dataset_stats
        training_results_file.write_text(_json.dumps(res, indent=2))
        log_event("INFO", "/train", f"Training results saved to {training_results_file}")
    return res

from app.utils.overlay_renderer import MultiAgentOverlayRenderer

overlay_renderer = MultiAgentOverlayRenderer()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), overlay_mode: Optional[str] = Form("YOLO Agent Active")):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file format.")
    
    return run_full_pipeline(img, file.filename, overlay_mode=overlay_mode or "YOLO Agent Active")

@app.post("/predict")
async def predict_image(file: UploadFile = File(...), strategy: Optional[str] = None):
    return await upload_file(file)

@app.post("/run_agents")
def run_agents_raw(image_b64: Optional[str] = Form(None), sample_name: Optional[str] = Form(None), overlay_mode: Optional[str] = Form("YOLO Agent Active")):
    if sample_name:
        sample_path = SAMPLE_IMAGES_DIR / sample_name
        if sample_path.exists():
            img = cv2.imread(str(sample_path))
        else:
            img = np.zeros((480, 640, 3), dtype=np.uint8)
    elif image_b64:
        header, encoded = image_b64.split(",", 1) if "," in image_b64 else ("", image_b64)
        nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        # Generate dark road sample image dynamically
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(img, (200, 260), (300, 320), (0, 0, 200), -1)

    return run_full_pipeline(img, sample_name or "sample_frame.jpg", overlay_mode=overlay_mode or "YOLO Agent Active")

@app.post("/run_conflict_resolution")
def run_conflict_resolution(req: ConflictResolveRequestSchema):
    try:
        res = resolution_engine.resolve(req.agent_outputs, req.conflicts, strategy=req.strategy)
        return res
    except Exception as e:
        logger.error(f"Error in run_conflict_resolution: {e}")
        raise HTTPException(status_code=500, detail=f"Conflict resolution failed: {e}")

@app.post("/evaluate_image_strategies")
def evaluate_image_strategies(req: ConflictResolveRequestSchema):
    """Runs all 10 conflict resolution algorithms specifically on the provided image agent outputs."""
    try:
        results = []
        action_counts = {}
        
        for st in settings.ALL_STRATEGIES:
            try:
                res = resolution_engine.resolve(req.agent_outputs, req.conflicts, strategy=st)
                results.append(res)
                act = res.get("final_decision", "UNKNOWN")
                action_counts[act] = action_counts.get(act, 0) + 1
            except Exception as st_err:
                logger.warning(f"Error evaluating strategy {st}: {st_err}")

        # Compute consensus metric
        top_action = max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else "UNKNOWN"
        top_votes = action_counts.get(top_action, 0)
        consensus_pct = round((top_votes / max(len(results), 1)) * 100.0, 1)

        return {
            "status": "success",
            "strategy_results": results,
            "action_counts": action_counts,
            "top_action": top_action,
            "consensus_pct": consensus_pct,
            "total_strategies": len(results)
        }
    except Exception as e:
        logger.error(f"Error evaluating image strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Strategy evaluation failed: {e}")

def run_full_pipeline(img: np.ndarray, filename: str, overlay_mode: str = "YOLO Agent Active") -> Dict[str, Any]:
    try:
        context = {}
        
        # 1. Object Agent (Primary YOLO, conf 0.3)
        out_obj = object_agent.run(img, context)
        
        # 2. Secondary Object Agent (Half-res, conf 0.45)
        out_sec_obj = secondary_agent.run(img, context)
        
        # 3. Lane Agent
        out_lane = lane_agent.run(img, context)
        
        # 4. Traffic Rule Agent (Independent YOLO, conf 0.5)
        out_traffic = traffic_agent.run(img, context)
        
        # 5. Scene Agent
        out_scene = scene_agent.run(img, context)
        
        # 6. Risk Agent (Independent YOLO, conf 0.25)
        out_risk = risk_agent.run(img, context)
        
        # 6 Independent Perception Agents in the Voting Pool
        voting_pool_outputs = [out_obj, out_sec_obj, out_lane, out_traffic, out_scene, out_risk]

        # 7. Centralized Planning Agent Baseline (sits outside voting pool)
        out_plan = planning_agent.run(img, {"prior_agent_outputs": voting_pool_outputs})
        
        # Detect Conflicts across voting pool
        conflicts = conflict_detector.detect_conflicts(voting_pool_outputs)

        # 8. Strategy Selector Agent (Meta Orchestrator)
        out_strat_agent = strategy_selector_agent.run(img, {
            "prior_agent_outputs": voting_pool_outputs,
            "conflicts": conflicts
        })
        
        all_agent_outputs = [out_obj, out_sec_obj, out_lane, out_traffic, out_scene, out_risk, out_plan, out_strat_agent]

        # Execute Conflict Resolution Engine with Auto-Selected Strategy on Voting Pool
        auto_selected_strategy = out_strat_agent.decision
        resolution = resolution_engine.resolve(voting_pool_outputs, conflicts, strategy=auto_selected_strategy)
        resolution["auto_selected_strategy"] = auto_selected_strategy
        resolution["selection_reasoning"] = out_strat_agent.reasoning
        resolution["centralized_planner_decision"] = out_plan.decision

        dict_outputs = [
            a.model_dump() if hasattr(a, 'model_dump') else (a.dict() if hasattr(a, 'dict') else a)
            for a in all_agent_outputs
        ]
        
        # Persist results
        try:
            save_prediction_and_conflicts(filename, dict_outputs, conflicts, resolution)
        except Exception as db_err:
            logger.warning(f"DB save warning: {db_err}")
        
        # Live inference path does not update reliability without ground truth labels.

        # Render Agent Overlay directly onto Image Frame
        rendered_img = img
        if img is not None and isinstance(img, np.ndarray) and img.size > 0:
            rendered_img = overlay_renderer.render_overlay(img, all_agent_outputs, overlay_mode=overlay_mode)
            _, buffer = cv2.imencode('.jpg', rendered_img)
            rendered_b64 = base64.b64encode(buffer).decode('utf-8')
            img_uri = f"data:image/jpeg;base64,{rendered_b64}"
        else:
            img_uri = ""

        return {
            "filename": filename,
            "agent_outputs": dict_outputs,
            "conflicts": conflicts,
            "resolution": resolution,
            "rendered_image": img_uri,
            "auto_selected_strategy": auto_selected_strategy,
            "active_overlay": overlay_mode
        }
    except Exception as e:
        logger.error(f"Error in run_full_pipeline: {e}")
        return {
            "filename": filename,
            "error": str(e),
            "is_fallback": True,
            "agent_outputs": [],
            "conflicts": [],
            "resolution": {
                "strategy": settings.DEFAULT_STRATEGY,
                "final_decision": "SLOW DOWN",
                "confidence": 0.80,
                "reasoning": f"Fallback due to execution exception: {e}",
                "winning_agent": "Fallback Safety Engine",
                "resolution_time_ms": 1.0
            },
            "rendered_image": ""
        }

@app.get("/get_metrics")
def get_metrics():
    import json as _json
    reliability_scores = reliability_engine.get_all_reliability_metrics()
    dataset_stats = dataset_mgr.generate_statistics()

    # Merge in persisted training results if available
    training_results_file = DATA_DIR / "training_results.json"
    training_metrics = {}
    persisted_ds_stats = None
    if training_results_file.exists():
        try:
            saved = _json.loads(training_results_file.read_text())
            training_metrics = saved.get("metrics", {})
            persisted_ds_stats = saved.get("dataset_statistics", None)
        except Exception:
            pass

    # Prefer persisted dataset stats (from actual training) over live scan
    effective_ds_stats = persisted_ds_stats if persisted_ds_stats else dataset_stats

    return {
        "agent_reliability": reliability_scores,
        "dataset_statistics": effective_ds_stats,
        "training_metrics": training_metrics,
    }

@app.get("/get_logs")
def get_logs(limit: int = 50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/history")
def get_history(limit: int = 30):
    return {
        "predictions": agent_memory.get_recent_history(limit),
        "conflicts": agent_memory.get_conflict_history(limit)
    }

@app.get("/experiments")
def get_experiments():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    
    results = [dict(r) for r in rows]
    if not results:
        # Run auto-benchmark on first fetch if empty
        results = benchmark_runner.run_benchmark(num_frames=10)
        
    chart_data = visualizer.generate_benchmark_chart_data(results)
    curves = visualizer.generate_roc_pr_curve_data()
    return {
        "experiments": results,
        "chart_data": chart_data,
        "curves": curves
    }

@app.post("/experiments/run")
def trigger_benchmark(num_frames: int = 15):
    res = benchmark_runner.run_benchmark(num_frames=num_frames)
    chart_data = visualizer.generate_benchmark_chart_data(res)
    return {"status": "success", "results": res, "chart_data": chart_data}

@app.get("/export")
def export_results():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM experiments")
    exp_rows = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM conflicts")
    conflict_rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    return {
        "exported_at": datetime.now().isoformat(),
        "experiments": exp_rows,
        "conflicts": conflict_rows
    }

@app.get("/sample_images")
def list_sample_images():
    files = list(SAMPLE_IMAGES_DIR.glob("*.jpg")) + list(SAMPLE_IMAGES_DIR.glob("*.png"))
    return [f.name for f in files]
