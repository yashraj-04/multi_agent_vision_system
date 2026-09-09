import os
from pathlib import Path
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROJECT_LOCAL_DATASET = BASE_DIR / "data" / "dataset"
DEFAULT_CUSTOM_DIR = Path(r"C:\Users\Yashraj Sharma\Downloads\road traffic.v1i.yolov11")

env_dataset = os.getenv("DATASET_DIR")
if env_dataset:
    DATASET_DIR = Path(env_dataset)
elif PROJECT_LOCAL_DATASET.exists() and (PROJECT_LOCAL_DATASET / "data.yaml").exists():
    DATASET_DIR = PROJECT_LOCAL_DATASET
elif DEFAULT_CUSTOM_DIR.exists():
    DATASET_DIR = DEFAULT_CUSTOM_DIR
else:
    DATASET_DIR = DATA_DIR / "dataset"

SAMPLE_IMAGES_DIR = DATA_DIR / "sample_images"
DB_PATH = DATA_DIR / "system.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Master Strategy Definitions
ALL_STRATEGIES = [
    "Majority Voting",
    "Confidence Weighted Voting",
    "Rule-Based Arbitration",
    "Leader Election",
    "Dynamic Reliability Scoring",
    "Bayesian Fusion",
    "Weighted Consensus",
    "Softmax-Weighted Selection",
    "Adaptive Reliability Learning",
    "Dynamic Entropy-Weighted Ensemble"
]

SELECTOR_STRATEGIES = [
    "Majority Voting",
    "Confidence Weighted Voting",
    "Rule-Based Arbitration",
    "Leader Election"
]

class Settings(BaseModel):
    PROJECT_NAME: str = "Conflict Resolution Strategies in Multi-Agent Vision Systems for Robotics"
    API_V1_STR: str = "/api/v1"
    
    # Vision LLM Configuration
    OLLAMA_HOST: str = Field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    VISION_MODEL: str = Field(default_factory=lambda: os.getenv("VISION_MODEL", "moondream"))
    SUPPORTED_VISION_MODELS: list[str] = [
        "moondream",
        "llava",
        "gemma3-vision",
        "qwen2.5-vl",
        "phi-vision"
    ]
    
    # Conflict Resolution Algorithms
    ALL_STRATEGIES: list[str] = ALL_STRATEGIES
    SELECTOR_STRATEGIES: list[str] = SELECTOR_STRATEGIES
    SUPPORTED_STRATEGIES: list[str] = ALL_STRATEGIES
    DEFAULT_STRATEGY: str = "Rule-Based Arbitration"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"

settings = Settings()
