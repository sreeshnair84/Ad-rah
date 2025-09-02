"""
Analytics Module for Adarah Digital Signage Platform
Provides real-time analytics, audience measurement, and performance insights
Essential for advertising effectiveness measurement and business optimization
"""

from .real_time_analytics import analytics_service, AnalyticsEvent, MetricType
from .audience_analytics import audience_analyzer, AudienceMetrics, DemographicData
from .performance_monitor import performance_monitor, PerformanceMetrics, KPIAlert

__all__ = [
    'analytics_service',
    'AnalyticsEvent',
    'MetricType',
    'audience_analyzer',
    'AudienceMetrics', 
    'DemographicData',
    'performance_monitor',
    'PerformanceMetrics',
    'KPIAlert'
]