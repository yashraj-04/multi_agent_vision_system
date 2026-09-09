# Conflict Resolution Strategies in Multi-Agent Vision Systems for Robotics

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://www.python.org/)
[![FastAPI: 0.100+](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React: 18+](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)
[![YOLOv8: Ultralytics](https://img.shields.io/badge/YOLOv8-Ultralytics-blueviolet.svg)](https://docs.ultralytics.com/)

A research-grade, production-quality autonomous vehicle perception platform. Instead of relying on a single monocular model, this architecture deploys **6 specialized, independent AI perception agents** analyzing the same camera frame. Disagreements and safety contradictions are detected automatically by a dedicated **Conflict Detector** and arbitrated using **10 selectable research-grade Conflict Resolution Algorithms**.

---

## 📐 System Architecture

```
                                  Camera / Video / Webcam Input
                                                │
                                                ▼
                                     ┌─────────────────────┐
                                     │ YOLOv8 Object Core  │
                                     └──────────┬──────────┘
                                                │
                                                ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                Independent Perception Agents                                │
 │                                                                                             │
 │  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────────────┐  │
 │  │ 1. Object Detection   │   │ 2. Lane Detection     │   │ 3. Traffic Rule Agent         │  │
 │  │    (YOLO Objects)     │   │    (OpenCV Geometry)  │   │    (Signal Compliance)        │  │
 │  └───────────────────────┘   └───────────────────────┘   └───────────────────────────────┘  │
 │  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────────────┐  │
 │  │ 4. Scene Understanding│   │ 5. Risk Assessment    │   │ 6. Planning Agent             │  │
 │  │    (VisionLLM/Ollama) │   │    (Collision / TTC)  │   │    (Control Synthesis)        │  │
 │  └───────────────────────┘   └───────────────────────┘   └───────────────────────────────┘  │
 └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                │
                                                ▼
                                   ┌───────────────────────────┐
                                   │     Conflict Detector     │
                                   │  (Semantic Cross-Check)   │
                                   └────────────┬──────────────┘
                                                │
                                                ▼
                                   ┌───────────────────────────┐
                                   │ Conflict Resolution Engine│
                                   │ (10 Selectable Algorithms)│
                                   └────────────┬──────────────┘
                                                │
                                                ▼
                                   ┌───────────────────────────┐
                                   │ Dynamic Reliability Store │
                                   │   & SQLite Persistence    │
                                   └────────────┬──────────────┘
                                                │
                                                ▼
                                   ┌───────────────────────────┐
                                   │ React + Vite Futuristic UI│
                                   └───────────────────────────┘
```

---

## 🧠 Perception Agents & Specializations

Each agent executes independently on the exact same frame, producing structured output containing `decision`, `confidence`, `reasoning`, `evidence`, `latency_ms`, and `timestamp`:

1. **Agent 1: Object Detection Agent**:
   - Detects vehicles, pedestrians, traffic lights, traffic signs, road obstacles, motorcycles, and bicycles with 2D bounding boxes.
2. **Agent 2: Lane Detection Agent**:
   - Extracts lane boundaries using OpenCV Canny/Hough transforms, computes lateral lane offset, and estimates road curvature (`LANE_CENTERED`, `CURVE_LEFT`, `CURVE_RIGHT`, `LANE_DEPARTURE_WARNING`).
3. **Agent 3: Traffic Rule Agent**:
   - Enforces legal priorities, speed limit signs (e.g. 60 km/h), stop signs, and traffic signal compliance (`MUST_STOP_RED_LIGHT`, `PROCEED_GREEN_LIGHT`, `SPEED_LIMIT_60`).
4. **Agent 4: Scene Understanding Agent (VisionLLM)**:
   - Uses the unified `VisionLLM` abstraction layer to interface with **Ollama** models (**Moondream** default, **LLaVA**, **Gemma 3 Vision**, **Qwen2.5-VL**, **Phi Vision**). Infers weather, surface traction, and hidden risks.
5. **Agent 5: Risk Assessment Agent**:
   - Computes physics-based spatial danger, Time-To-Collision (TTC in seconds), pedestrian collision risk, and emergency levels (`CRITICAL`, `HIGH`, `MODERATE`, `LOW`).
6. **Agent 6: Planning Agent**:
   - Fuses prior agent outputs to generate overall control decisions (`GO`, `STOP`, `TURN LEFT`, `TURN RIGHT`, `SLOW DOWN`, `CHANGE LANE`, `EMERGENCY BRAKE`).

---

## ⚡ 10 Conflict Resolution Strategies

Selectable directly from the React dashboard:

1. **Majority Voting**: Modal action vote across all proposals.
2. **Confidence Weighted Voting**: Sums confidence scores per proposed action.
3. **Rule-Based Arbitration**: Safety hierarchy override (e.g. Risk Agent & Traffic Rules override speed suggestions).
4. **Leader Election**: Dynamic election of top-performing agent based on current context.
5. **Dynamic Reliability Scoring**: Weighted vote based on exponential moving averages of historical agent accuracy.
6. **Bayesian Fusion**: Log-likelihood posterior probability updates using historical confusion matrix priors.
7. **Weighted Consensus**: Iterative weight convergence algorithm.
8. **Hybrid Arbitration**: Safety Gatekeeper filter combined with Dynamic Reliability Voting.
9. **Adaptive Reliability Learning**: Softmax Q-score action selection based on past conflict rewards.
10. **Dynamic Entropy-Weighted Ensemble**: Weights decisions inversely to agent decision entropy (rewarding low uncertainty).

---

## 📁 Repository Structure

```
multi_agent_vision_system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application & route handlers
│   │   ├── config.py                   # Settings, VisionLLM models, strategy definitions
│   │   ├── database.py                 # SQLite ORM & tables (predictions, conflicts, metrics)
│   │   ├── vision_llm.py               # VisionLLM abstraction layer (Ollama + smart CV fallback)
│   │   ├── dataset_manager.py          # Kaggle dataset parser, split, augment, synthetic generator
│   │   ├── yolo_trainer.py             # Ultralytics YOLOv8 detector & training engine
│   │   ├── agents/
│   │   │   ├── base_agent.py           # Base agent abstract class & Pydantic output schema
│   │   │   ├── object_detection_agent.py
│   │   │   ├── lane_detection_agent.py
│   │   │   ├── traffic_rule_agent.py
│   │   │   ├── scene_understanding_agent.py
│   │   │   ├── risk_assessment_agent.py
│   │   │   └── planning_agent.py
│   │   ├── conflict/
│   │   │   ├── conflict_detector.py      # Automated cross-agent contradiction detector
│   │   │   ├── resolution_engine.py      # 10 Conflict Resolution Strategies implementation
│   │   │   └── dynamic_reliability.py    # Online reliability score update engine
│   │   ├── memory/
│   │   │   └── agent_memory.py           # Historical decision & conflict persistence
│   │   ├── experiments/
│   │   │   └── benchmark_runner.py       # Multi-strategy research benchmark runner
│   │   └── utils/
│   │       ├── logger.py                 # Structured logger
│   │       └── visualization.py          # Analytical chart data generator
│   ├── data/                           # Dataset storage & SQLite system.db
│   ├── requirements.txt
│   └── test_system.py                  # End-to-end verification test suite
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── Navbar.jsx              # Navigation header with model & strategy selectors
│   │   │   ├── PerceptionDashboard.jsx   # Live frame studio, webcam, overlay canvas
│   │   │   ├── AgentStatusCards.jsx      # Live agent output cards
│   │   │   ├── ConflictViewer.jsx        # Conflict alert panel
│   │   │   ├── ResolutionEnginePanel.jsx # Arbitration output & 10 strategy dropdown
│   │   │   ├── VisionLLMModal.jsx        # VisionLLM reasoning inspector
│   │   │   ├── ExperimentBenchmark.jsx   # Benchmark metrics comparison table
│   │   │   └── DatasetTrainerPanel.jsx   # YOLO training & dataset split management
│   │   └── services/
│   │       └── api.js                  # Axios client wrapper
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
├── Dockerfile
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Installation

```bash
# Clone repository
git clone https://github.com/user/multi_agent_vision_system.git
cd multi_agent_vision_system

# Backend setup
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Launch FastAPI Backend

```bash
# From backend directory
uvicorn app.main:app --reload --port 8000
```
- API Documentation: `http://localhost:8000/docs`

### 3. Launch React Frontend

```bash
# From frontend directory
cd ../frontend
npm install
npm run dev
```
- Open browser at `http://localhost:3000`

---

## 🤖 Ollama Local LLM Setup (Optional)

To connect to local Ollama Vision models:

1. Install Ollama from [ollama.com](https://ollama.com).
2. Pull default Moondream model:
   ```bash
   ollama pull moondream
   ```
3. Set active model in environment or select via UI header:
   ```bash
   export VISION_MODEL=moondream
   ```

*Note: If Ollama is offline, the system automatically uses an intelligent computer-vision fallback module so all functionality remains 100% operational out-of-the-box.*

---

## 📊 Research Experiments & Metrics Exporter

Click **"Run Multi-Strategy Benchmark"** in the Research Benchmarks tab to run empirical benchmarks comparing all 10 Conflict Resolution Strategies across:
- **Accuracy**, **Precision**, **Recall**, **F1 Score**, **mAP**
- **FPS** and **Average Latency (ms)**
- **Consensus Time (ms)** & **Conflict Resolution Time (ms)**
- **Conflict Frequency** & **Decision Stability Index**

Export full research datasets via `http://localhost:8000/export` or the frontend Download button.

---

## 📜 License
MIT License. Created for advanced research in autonomous robotics and multi-agent AI alignment.
