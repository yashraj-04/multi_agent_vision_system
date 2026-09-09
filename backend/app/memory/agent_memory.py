import json
from typing import Dict, Any, List
from app.database import get_db_connection
from app.utils.logger import logger

class AgentMemory:
    """
    Stores and retrieves agent decision history, conflict events, performance trends, and reasoning logs.
    """
    def get_recent_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.timestamp, p.image_name, p.agent_outputs, r.strategy_used, r.final_decision, r.confidence, r.reasoning
            FROM predictions p
            LEFT JOIN resolutions r ON p.id = r.frame_id
            ORDER BY p.id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for r in rows:
            outputs = json.loads(r["agent_outputs"]) if r["agent_outputs"] else {}
            history.append({
                "id": r["id"],
                "timestamp": r["timestamp"],
                "image_name": r["image_name"],
                "agent_outputs": outputs,
                "strategy": r["strategy_used"] or "N/A",
                "final_decision": r["final_decision"] or "GO",
                "confidence": r["confidence"] or 0.9,
                "reasoning": r["reasoning"] or ""
            })
        return history

    def get_conflict_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.timestamp, c.conflict_type, c.agents_involved, c.disagreement_details, r.strategy_used, r.final_decision
            FROM conflicts c
            LEFT JOIN resolutions r ON c.id = r.conflict_id
            ORDER BY c.id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        conflicts = []
        for r in rows:
            conflicts.append({
                "id": r["id"],
                "timestamp": r["timestamp"],
                "type": r["conflict_type"],
                "agents": json.loads(r["agents_involved"]) if r["agents_involved"] else [],
                "details": json.loads(r["disagreement_details"]) if r["disagreement_details"] else {},
                "resolved_strategy": r["strategy_used"],
                "final_decision": r["final_decision"]
            })
        return conflicts
