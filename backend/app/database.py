import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import DB_PATH
from app.utils.logger import logger

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Predictions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        image_name TEXT,
        agent_outputs TEXT NOT NULL
    );
    """)
    
    # Conflicts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conflicts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        frame_id INTEGER,
        conflict_type TEXT NOT NULL,
        agents_involved TEXT NOT NULL,
        disagreement_details TEXT NOT NULL
    );
    """)
    
    # Resolutions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resolutions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        frame_id INTEGER,
        conflict_id INTEGER,
        strategy_used TEXT NOT NULL,
        final_decision TEXT NOT NULL,
        confidence REAL NOT NULL,
        reasoning TEXT,
        resolution_time_ms REAL NOT NULL
    );
    """)
    
    # Agent Metrics & Reliability Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_reliability (
        agent_name TEXT PRIMARY KEY,
        reliability_score REAL NOT NULL,
        total_decisions INTEGER DEFAULT 0,
        successful_decisions INTEGER DEFAULT 0,
        failed_decisions INTEGER DEFAULT 0,
        conflict_count INTEGER DEFAULT 0,
        false_positives INTEGER DEFAULT 0,
        false_negatives INTEGER DEFAULT 0,
        avg_confidence REAL DEFAULT 0.0,
        avg_latency_ms REAL DEFAULT 0.0,
        last_updated TEXT NOT NULL
    );
    """)
    
    # Experiments Benchmark Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        run_id TEXT,
        seed INTEGER,
        config_snapshot TEXT,
        strategy TEXT NOT NULL,
        accuracy REAL,
        precision_score REAL,
        recall REAL,
        f1_score REAL,
        fps REAL,
        avg_latency_ms REAL,
        consensus_time_ms REAL,
        conflict_resolution_time_ms REAL,
        conflict_frequency REAL,
        reliability_score REAL,
        agreement_rate REAL,
        avg_confidence REAL,
        decision_stability REAL,
        sample_count INTEGER
    );
    """)
    
    # Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        level TEXT NOT NULL,
        endpoint TEXT,
        message TEXT NOT NULL
    );
    """)
    
    # Seed initial agent reliability scores if empty
    default_agents = [
        "Object Detection Agent",
        "Lane Detection Agent",
        "Traffic Rule Agent",
        "Scene Understanding Agent",
        "Risk Assessment Agent",
        "Planning Agent"
    ]
    for agent in default_agents:
        cursor.execute("""
        INSERT OR IGNORE INTO agent_reliability 
        (agent_name, reliability_score, total_decisions, successful_decisions, failed_decisions, conflict_count, false_positives, false_negatives, avg_confidence, avg_latency_ms, last_updated)
        VALUES (?, 0.90, 100, 92, 8, 12, 5, 3, 0.88, 25.0, ?);
        """, (agent, datetime.now().isoformat()))
        
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def save_prediction_and_conflicts(image_name: str, agent_outputs: Dict[str, Any], conflicts: List[Dict[str, Any]], resolution: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO predictions (timestamp, image_name, agent_outputs) VALUES (?, ?, ?)",
        (now, image_name, json.dumps(agent_outputs))
    )
    frame_id = cursor.lastrowid
    
    conflict_id = None
    if conflicts:
        for c in conflicts:
            cursor.execute(
                "INSERT INTO conflicts (timestamp, frame_id, conflict_type, agents_involved, disagreement_details) VALUES (?, ?, ?, ?, ?)",
                (now, frame_id, c.get("type", "General"), json.dumps(c.get("agents", [])), json.dumps(c))
            )
            conflict_id = cursor.lastrowid
            
    if resolution:
        cursor.execute(
            "INSERT INTO resolutions (timestamp, frame_id, conflict_id, strategy_used, final_decision, confidence, reasoning, resolution_time_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (now, frame_id, conflict_id, resolution.get("strategy"), resolution.get("final_decision"), resolution.get("confidence", 0.0), resolution.get("reasoning", ""), resolution.get("resolution_time_ms", 0.0))
        )
        
    conn.commit()
    conn.close()

def log_event(level: str, endpoint: str, message: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (timestamp, level, endpoint, message) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), level, endpoint, message)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log event: {e}")
