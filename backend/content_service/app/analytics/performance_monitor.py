"""Performance monitoring stub for analytics package."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any

@dataclass
class PerformanceMetrics:
    timestamp: datetime = field(default_factory=datetime.utcnow)
    kpi_score: float = 100.0
    alerts: int = 0

class PerformanceMonitor:
    def get_metrics(self) -> PerformanceMetrics:
        return PerformanceMetrics()

performance_monitor = PerformanceMonitor()

@dataclass
class KPIAlert:
    alert_id: str
    message: str
    severity: str = "medium"

__all__ = ["performance_monitor", "PerformanceMetrics", "KPIAlert"]
