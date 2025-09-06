"""
Sample analytics data seeder for testing the dashboard
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List

try:
    from app.analytics.real_time_analytics import analytics_service, MetricType, AnalyticsEvent
except ImportError:
    # Create simple mock objects for seeding
    class MetricType:
        IMPRESSION = "impression"
        INTERACTION = "interaction" 
        AUDIENCE = "audience"
        DWELL_TIME = "dwell_time"
        
    class AnalyticsEvent:
        CONTENT_VIEW_START = "content_view_start"
        CONTENT_VIEW_END = "content_view_end"
        CONTENT_INTERACTION = "content_interaction"
        AUDIENCE_DETECTED = "audience_detected"
        
    # Mock analytics service
    class MockAnalyticsService:
        async def record_batch_metrics(self, events):
            print(f"Mock: Would record {len(events)} events")
            return {"success": True, "events_recorded": len(events)}
            
        async def get_real_time_metrics(self):
            return {"success": True, "metrics": []}
    
    analytics_service = MockAnalyticsService()

async def seed_sample_analytics_data():
    """Seed sample analytics data for testing the dashboard"""
    
    # Sample device IDs
    device_ids = ["DEVICE_001", "DEVICE_002", "DEVICE_003", "DEVICE_004"]
    
    # Sample content IDs
    content_ids = ["content_1", "content_2", "content_3", "content_4", "content_5"]
    
    # Sample campaign IDs
    campaign_ids = ["campaign_a", "campaign_b", "campaign_c"]
    
    # Sample advertiser IDs
    advertiser_ids = ["advertiser_1", "advertiser_2", "advertiser_3"]
    
    # Generate data for the last 24 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    events_to_record = []
    
    # Generate random events
    for _ in range(1000):  # Generate 1000 sample events
        
        # Random timestamp within the last 24 hours
        random_time = start_time + timedelta(
            seconds=random.randint(0, int((end_time - start_time).total_seconds()))
        )
        
        # Random device and content
        device_id = random.choice(device_ids)
        content_id = random.choice(content_ids)
        campaign_id = random.choice(campaign_ids)
        advertiser_id = random.choice(advertiser_ids)
        
        # Generate different types of events
        event_types = [
            {
                "metric_type": MetricType.IMPRESSION.value,
                "event_type": AnalyticsEvent.CONTENT_VIEW_START.value,
                "value": 1.0,
                "revenue_impact": random.uniform(0.01, 0.50)  # Small revenue per impression
            },
            {
                "metric_type": MetricType.INTERACTION.value,
                "event_type": AnalyticsEvent.CONTENT_INTERACTION.value,
                "value": 1.0,
                "duration_seconds": random.uniform(1.0, 30.0),
                "revenue_impact": random.uniform(0.05, 1.00)  # Higher revenue for interactions
            },
            {
                "metric_type": MetricType.AUDIENCE.value,
                "event_type": AnalyticsEvent.AUDIENCE_DETECTED.value,
                "value": random.randint(1, 5),  # 1-5 people detected
                "audience_count": random.randint(1, 5),
                "demographic_data": {
                    "user_id": f"user_{random.randint(1000, 9999)}",
                    "age_group": random.choice(["18-25", "26-35", "36-45", "46-55", "55+"]),
                    "gender": random.choice(["male", "female", "other"]),
                    "interest_category": random.choice(["tech", "fashion", "food", "travel", "sports"])
                }
            },
            {
                "metric_type": MetricType.DWELL_TIME.value,
                "event_type": AnalyticsEvent.CONTENT_VIEW_END.value,
                "value": random.uniform(5.0, 120.0),  # 5 seconds to 2 minutes
                "duration_seconds": random.uniform(5.0, 120.0)
            }
        ]
        
        # Select random event type
        event_data = random.choice(event_types)
        
        # Add common fields
        event_data.update({
            "device_id": device_id,
            "content_id": content_id,
            "campaign_id": campaign_id,
            "advertiser_id": advertiser_id,
            "timestamp": random_time.isoformat(),
            "location": {
                "lat": random.uniform(40.0, 41.0),  # Sample NYC area coordinates
                "lng": random.uniform(-74.5, -73.5)
            },
            "device_capabilities": {
                "screen_size": random.choice(["32inch", "42inch", "55inch", "65inch"]),
                "resolution": random.choice(["1920x1080", "3840x2160", "2560x1440"]),
                "touch_enabled": random.choice([True, False])
            },
            "network_conditions": {
                "connection_type": random.choice(["wifi", "ethernet", "cellular"]),
                "speed_mbps": random.uniform(10.0, 100.0),
                "latency_ms": random.uniform(10.0, 100.0)
            },
            "data_quality_score": random.uniform(0.8, 1.0),
            "verification_level": random.choice(["standard", "verified", "premium"])
        })
        
        events_to_record.append(event_data)
    
    # Record all events in batch
    try:
        result = await analytics_service.record_batch_metrics(events_to_record)
        print(f"✅ Successfully seeded {len(events_to_record)} analytics events")
        print(f"📊 Batch recording result: {result}")
        
        # Get some sample real-time metrics to verify
        metrics = await analytics_service.get_real_time_metrics()
        if metrics.get("success"):
            print(f"📈 Current metrics count: {len(metrics.get('metrics', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error seeding analytics data: {e}")
        return False

async def seed_system_health_data():
    """Seed system health metrics for devices"""
    
    device_ids = ["DEVICE_001", "DEVICE_002", "DEVICE_003", "DEVICE_004"]
    
    for device_id in device_ids:
        # Generate system health metrics for each device
        health_events = []
        
        # Generate health data for the last 6 hours (every 5 minutes)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=6)
        current_time = start_time
        
        while current_time <= end_time:
            health_event = {
                "metric_type": "performance",
                "event_type": "system_metrics",
                "device_id": device_id,
                "timestamp": current_time.isoformat(),
                "data": {
                    "cpu": random.uniform(20.0, 80.0),
                    "memory": random.uniform(30.0, 90.0),
                    "storage": random.uniform(10.0, 70.0),
                    "network_latency": random.uniform(10.0, 100.0),
                    "temperature": random.uniform(35.0, 65.0),
                    "uptime_hours": random.uniform(100.0, 720.0)
                },
                "value": 1.0
            }
            health_events.append(health_event)
            current_time += timedelta(minutes=5)
        
        # Record health events
        try:
            await analytics_service.record_batch_metrics(health_events)
            print(f"✅ Seeded health data for {device_id}: {len(health_events)} metrics")
        except Exception as e:
            print(f"❌ Error seeding health data for {device_id}: {e}")

async def main():
    """Main function to seed all sample data"""
    print("🌱 Starting analytics data seeding...")
    
    # Seed main analytics data
    await seed_sample_analytics_data()
    
    # Seed system health data
    await seed_system_health_data()
    
    print("✅ Analytics data seeding completed!")

if __name__ == "__main__":
    asyncio.run(main())
