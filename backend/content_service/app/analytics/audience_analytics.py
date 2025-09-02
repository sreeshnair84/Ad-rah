"""Audience analytics compatibility shim.

Provides minimal implementations used by imports across the codebase so the
analytics package can be imported in environments where full implementation
is not present.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DemographicData:
    age_group: Optional[str] = None
    gender: Optional[str] = None
    other: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AudienceMetrics:
    timestamp: datetime = field(default_factory=datetime.utcnow)
    audience_count: int = 0
    average_dwell: float = 0.0

class AudienceAnalyzer:
    def analyze(self, events: List[Dict[str, Any]]) -> AudienceMetrics:
        # Minimal heuristic: count events with audience_count
        total = 0
        count = 0
        for e in events:
            a = e.get('audience_count')
            if a:
                total += a
                count += 1

        avg = (total / count) if count else 0
        return AudienceMetrics(audience_count=total, average_dwell=avg)

audience_analyzer = AudienceAnalyzer()

__all__ = ["audience_analyzer", "AudienceMetrics", "DemographicData"]
