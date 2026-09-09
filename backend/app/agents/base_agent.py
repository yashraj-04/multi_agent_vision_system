import time
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentOutput(BaseModel):
    agent_name: str
    decision: str
    confidence: float
    reasoning: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    latency_ms: float
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def _analyze(self, image: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Internal agent specific analysis method."""
        pass

    def run(self, image: Any, context: Optional[Dict[str, Any]] = None) -> AgentOutput:
        """Executes agent analysis and measures execution latency."""
        start_time = time.time()
        result = self._analyze(image, context)
        latency = (time.time() - start_time) * 1000.0
        
        return AgentOutput(
            agent_name=self.name,
            decision=result.get("decision", "UNKNOWN"),
            confidence=round(result.get("confidence", 0.8), 3),
            reasoning=result.get("reasoning", "Analysis complete."),
            evidence=result.get("evidence", {}),
            latency_ms=round(latency, 2),
            timestamp=datetime.now().isoformat()
        )
