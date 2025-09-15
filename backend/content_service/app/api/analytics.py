"""
Analytics API endpoints for real-time metrics and analytics data
Provides REST API endpoints that connect to the real-time analytics service
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import json
import asyncio
from datetime import datetime, timedelta
import logging

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Import dependencies
try:
    from app.security.device_auth import authenticate_device
except ImportError:
    # Fallback authentication function
    def authenticate_device():
        return {"device_id": "fallback_device"}

from app.analytics.real_time_analytics import analytics_service, MetricType, AggregationPeriod
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Request/Response Models
class AnalyticsEventRequest(BaseModel):
    metric_type: str = Field(..., description="Type of metric (impression, interaction, etc.)")
    event_type: str = Field(..., description="Specific event type")
    device_id: str = Field(..., description="Device identifier")
    content_id: Optional[str] = Field(None, description="Content identifier")
    campaign_id: Optional[str] = Field(None, description="Campaign identifier")
    value: float = Field(1.0, description="Metric value")
    count: int = Field(1, description="Event count")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    timestamp: Optional[str] = Field(None, description="Event timestamp")
    location: Optional[Dict[str, float]] = Field(None, description="Geographic location")
    audience_count: Optional[int] = Field(None, description="Audience size")
    demographic_data: Optional[Dict[str, Any]] = Field(None, description="Demographic information")
    device_capabilities: Optional[Dict[str, Any]] = Field(None, description="Device capabilities")
    network_conditions: Optional[Dict[str, Any]] = Field(None, description="Network conditions")
    content_metadata: Optional[Dict[str, Any]] = Field(None, description="Content metadata")
    advertiser_id: Optional[str] = Field(None, description="Advertiser identifier")
    host_id: Optional[str] = Field(None, description="Host company identifier")
    revenue_impact: Optional[float] = Field(None, description="Revenue impact")
    data_quality_score: float = Field(1.0, description="Data quality score")
    verification_level: str = Field("standard", description="Verification level")
    confidence_interval: Optional[float] = Field(None, description="Confidence interval")

class BatchAnalyticsRequest(BaseModel):
    events: List[AnalyticsEventRequest] = Field(..., description="List of analytics events")

class RealTimeMetricsRequest(BaseModel):
    device_ids: Optional[List[str]] = Field(None, description="Filter by device IDs")
    period: str = Field("minute", description="Aggregation period")

class DeviceAnalyticsRequest(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    hours: int = Field(24, description="Number of hours to analyze")

class CampaignAnalyticsRequest(BaseModel):
    campaign_id: str = Field(..., description="Campaign identifier")
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")

class SubscriptionRequest(BaseModel):
    subscriber_id: str = Field(..., description="Unique subscriber identifier")
    metric_types: Optional[List[str]] = Field(None, description="Specific metric types to subscribe to")

# WebSocket connection manager for real-time streaming
class AnalyticsConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            logger.info(f"Analytics client connected: {client_id}")
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection for {client_id}: {e}")
            raise
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]
        logger.info(f"Analytics client disconnected: {client_id}")
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                # Check if WebSocket is in connected state
                if hasattr(websocket, 'client_state') and websocket.client_state.value == 1:  # CONNECTED state
                    await websocket.send_text(json.dumps(message, cls=DateTimeEncoder))
                else:
                    logger.warning(f"WebSocket for {client_id} is not in connected state")
                    self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                # Check if WebSocket is in connected state
                if hasattr(connection, 'client_state') and connection.client_state.value == 1:  # CONNECTED state
                    await connection.send_text(json.dumps(message, cls=DateTimeEncoder))
                else:
                    disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

# Global connection manager
connection_manager = AnalyticsConnectionManager()

# REST API Endpoints

@router.post("/event")
async def record_analytics_event(
    event_request: AnalyticsEventRequest,
    device_info: dict = Depends(authenticate_device)
):
    """Record a single analytics event"""
    try:
        # Convert request to analytics service format
        event_data = event_request.model_dump(exclude_unset=True)
        
        # Add device info if not provided
        if not event_data.get("device_id"):
            event_data["device_id"] = device_info.get("device_id", "unknown")
        
        # Record the event
        result = await analytics_service.record_metric(event_data)
        
        # Broadcast to WebSocket subscribers only if there are active connections
        if connection_manager.active_connections:
            await connection_manager.broadcast({
                "type": "metric_event",
                "event": {
                    "metric_type": event_request.metric_type,
                    "event_type": event_request.event_type,
                    "device_id": event_data["device_id"],
                    "value": event_request.value,
                    "timestamp": event_request.timestamp or datetime.utcnow().isoformat()
                }
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to record analytics event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/events/batch")
async def record_batch_analytics_events(
    batch_request: BatchAnalyticsRequest,
    device_info: dict = Depends(authenticate_device)
):
    """Record multiple analytics events efficiently"""
    try:
        # Convert batch request to analytics service format
        events_data = []
        device_id = device_info.get("device_id", "unknown")
        
        for event_request in batch_request.events:
            event_data = event_request.model_dump(exclude_unset=True)
            if not event_data.get("device_id"):
                event_data["device_id"] = device_id
            events_data.append(event_data)
        
        # Record the batch
        result = await analytics_service.record_batch_metrics(events_data)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to record batch analytics events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/real-time")
async def get_real_time_metrics(
    device_ids: Optional[str] = None,
    period: str = "minute"
):
    """Get real-time aggregated metrics"""
    try:
        # Parse device IDs
        device_id_list = None
        if device_ids:
            device_id_list = [d.strip() for d in device_ids.split(",")]
        
        # Convert period string to enum
        try:
            aggregation_period = AggregationPeriod(period)
        except ValueError:
            aggregation_period = AggregationPeriod.MINUTE
        
        # Get metrics
        result = await analytics_service.get_real_time_metrics(
            device_ids=device_id_list,
            period=aggregation_period
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/device/{device_id}")
async def get_device_analytics(
    device_id: str,
    hours: int = 24,
    device_info: dict = Depends(authenticate_device)
):
    """Get comprehensive analytics for a specific device"""
    try:
        result = await analytics_service.get_device_analytics(device_id, hours)
        return result
        
    except Exception as e:
        logger.error(f"Failed to get device analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/campaign/{campaign_id}")
async def get_campaign_analytics(
    campaign_id: str,
    start_date: str,
    end_date: str,
    device_info: dict = Depends(authenticate_device)
):
    """Get comprehensive campaign performance analytics"""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        result = await analytics_service.get_campaign_analytics(
            campaign_id, start_dt, end_dt
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to get campaign analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe")
async def subscribe_to_real_time_updates(
    subscription_request: SubscriptionRequest,
    device_info: dict = Depends(authenticate_device)
):
    """Subscribe to real-time analytics updates"""
    try:
        # Parse metric types
        metric_types = None
        if subscription_request.metric_types:
            metric_types = [MetricType(mt) for mt in subscription_request.metric_types]
        
        result = await analytics_service.subscribe_to_real_time_updates(
            subscription_request.subscriber_id,
            metric_types or []
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to subscribe to updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/subscribe/{subscriber_id}")
async def unsubscribe_from_updates(
    subscriber_id: str,
    device_info: dict = Depends(authenticate_device)
):
    """Unsubscribe from real-time analytics updates"""
    try:
        result = await analytics_service.unsubscribe_from_updates(subscriber_id)
        return result
        
    except Exception as e:
        logger.error(f"Failed to unsubscribe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def analytics_health_check():
    """Check analytics service health"""
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/dashboard")
async def get_dashboard_analytics(
    timeRange: str = Query("24h", description="Time range: 1h, 24h, 7d, 30d"),
    device: str = Query("all", description="Device ID or 'all' for all devices"),
    device_info: dict = Depends(authenticate_device)
):
    """Get comprehensive analytics dashboard data with real aggregated metrics"""
    
    # Parse time range
    time_delta_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    
    if timeRange not in time_delta_map:
        raise HTTPException(status_code=400, detail="Invalid time range")
    
    end_time = datetime.utcnow()
    start_time = end_time - time_delta_map[timeRange]
    
    try:
        # Import required services
        from app.repo import repo
        
        # Get real device data from database
        devices_list = await repo.list_digital_screens() if hasattr(repo, 'list_digital_screens') else []
        
        # Filter by device if specified
        if device != "all":
            devices_list = [d for d in devices_list if d.get("id") == device or d.get("device_id") == device]
        
        # Get real analytics data from service
        dashboard_data = await analytics_service.get_dashboard_data(
            device_filter=device if device != "all" else None,
            start_time=start_time,
            end_time=end_time
        )
        
        # Enhance device data with real heartbeats and content status
        enhanced_devices = []
        for device_data in dashboard_data.get("devices", []):
            device_id = device_data.get("deviceId")
            
            # Get latest heartbeat data
            try:
                latest_heartbeat = await repo.get_device_heartbeats(device_id, 1) if hasattr(repo, 'get_device_heartbeats') else []
                heartbeat = latest_heartbeat[0] if latest_heartbeat else None
            except:
                heartbeat = None
            
            # Get current content being played
            try:
                current_content = await repo.get_device_current_content(device_id) if hasattr(repo, 'get_device_current_content') else None
            except:
                current_content = None
            
            # Get device registration info
            try:
                device_info_db = await repo.get_digital_screen(device_id) if hasattr(repo, 'get_digital_screen') else {}
            except:
                device_info_db = {}
            
            # Calculate real system health from heartbeat data
            system_health = {
                "cpuUsage": heartbeat.get("cpu_usage", 0) if heartbeat else device_data.get("systemHealth", {}).get("cpuUsage", 0),
                "memoryUsage": heartbeat.get("memory_usage", 0) if heartbeat else device_data.get("systemHealth", {}).get("memoryUsage", 0),
                "diskUsage": heartbeat.get("disk_usage", 0) if heartbeat else device_data.get("systemHealth", {}).get("diskUsage", 0),
                "temperature": heartbeat.get("temperature", 0) if heartbeat else device_data.get("systemHealth", {}).get("temperature", 35),
                "networkLatency": heartbeat.get("network_latency", 0) if heartbeat else device_data.get("systemHealth", {}).get("networkLatency", 50),
                "overallScore": heartbeat.get("performance_score", 0.8) if heartbeat else device_data.get("systemHealth", {}).get("overallScore", 0.8),
                "status": heartbeat.get("health_status", "good") if heartbeat else device_data.get("systemHealth", {}).get("status", "good")
            }
            
            # Real content information
            content_info = None
            if current_content:
                content_info = {
                    "id": current_content.get("content_id", ""),
                    "name": current_content.get("content_name", ""),
                    "type": current_content.get("content_type", ""),
                    "startTime": current_content.get("start_time", datetime.utcnow().isoformat()),
                    "duration": current_content.get("duration", 0),
                    "progress": current_content.get("progress", 0)
                }
            
            enhanced_device = {
                "deviceId": device_id,
                "deviceName": device_info_db.get("name", device_data.get("deviceName", f"Device {device_id[:8]}")),
                "isOnline": heartbeat is not None and (datetime.utcnow() - datetime.fromisoformat(heartbeat.get("timestamp", datetime.utcnow().isoformat()).replace('Z', '+00:00'))).seconds < 300 if heartbeat else device_data.get("isOnline", False),
                "lastHeartbeat": heartbeat.get("timestamp", datetime.utcnow().isoformat()) if heartbeat else device_data.get("lastHeartbeat", datetime.utcnow().isoformat()),
                "location": device_info_db.get("location", device_data.get("location", "Unknown")),
                "currentContent": content_info,
                "systemHealth": system_health,
                "contentMetrics": device_data.get("contentMetrics", {
                    "impressions": 0,
                    "interactions": 0,
                    "completions": 0,
                    "errors": 0,
                    "averageLoadTime": 0
                }),
                "audienceMetrics": device_data.get("audienceMetrics", {
                    "currentCount": 0,
                    "totalDetections": 0,
                    "averageDwellTime": 0,
                    "peakCount": 0,
                    "detectionConfidence": 0.8
                }),
                "monetization": device_data.get("monetization", {
                    "totalRevenue": 0,
                    "adImpressions": 0,
                    "clickthroughRate": 0,
                    "averageCPM": 0
                })
            }
            enhanced_devices.append(enhanced_device)
        
        # Calculate real summary statistics
        total_devices = len(enhanced_devices)
        online_devices = len([d for d in enhanced_devices if d["isOnline"]])
        total_revenue = sum(d["monetization"]["totalRevenue"] for d in enhanced_devices)
        total_impressions = sum(d["contentMetrics"]["impressions"] for d in enhanced_devices)
        total_interactions = sum(d["contentMetrics"]["interactions"] for d in enhanced_devices)
        total_audience = sum(d["audienceMetrics"]["currentCount"] for d in enhanced_devices)
        average_health = sum(d["systemHealth"]["overallScore"] for d in enhanced_devices) / total_devices if total_devices > 0 else 0
        average_engagement = (total_interactions / total_impressions * 100) if total_impressions > 0 else 0
        
        enhanced_summary = {
            "totalDevices": total_devices,
            "onlineDevices": online_devices,
            "totalRevenue": total_revenue,
            "totalImpressions": total_impressions,
            "averageEngagement": average_engagement,
            "totalAudience": total_audience,
            "averageHealth": average_health
        }
        
        return {
            "devices": enhanced_devices,
            "summary": enhanced_summary,
            "timeSeriesData": dashboard_data.get("time_series", []),
            "timeRange": timeRange,
            "generatedAt": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")

# WebSocket endpoint for real-time streaming
@router.websocket("/stream")
async def analytics_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time analytics streaming"""
    client_id = f"client_{datetime.now().timestamp()}"
    
    try:
        await connection_manager.connect(websocket, client_id)
        
        # Send initial connection success message
        await connection_manager.send_personal_message({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat()
        }, client_id)
        
        # Send initial metrics
        initial_metrics = await analytics_service.get_real_time_metrics()
        if initial_metrics.get("success"):
            await connection_manager.send_personal_message({
                "type": "metrics_update",
                "metrics": initial_metrics["metrics"],
                "timestamp": datetime.utcnow().isoformat()
            }, client_id)
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "subscribe_metrics":
                    # Client wants to subscribe to specific metrics
                    metric_types = message.get("metric_types", [])
                    connection_manager.subscriptions[client_id] = metric_types
                    
                    await connection_manager.send_personal_message({
                        "type": "subscription_confirmed",
                        "metric_types": metric_types,
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)
                
                elif message.get("type") == "request_current_metrics":
                    # Client requests current metrics
                    current_metrics = await analytics_service.get_real_time_metrics()
                    if current_metrics.get("success"):
                        await connection_manager.send_personal_message({
                            "type": "metrics_update",
                            "metrics": current_metrics["metrics"],
                            "timestamp": datetime.utcnow().isoformat()
                        }, client_id)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                # Only send error message if WebSocket is still connected
                if client_id in connection_manager.active_connections:
                    try:
                        websocket = connection_manager.active_connections[client_id]
                        if websocket.client_state.value == 1:  # CONNECTED state
                            await connection_manager.send_personal_message({
                                "type": "error",
                                "message": "Invalid JSON format",
                                "timestamp": datetime.utcnow().isoformat()
                            }, client_id)
                    except Exception as send_error:
                        logger.error(f"Failed to send JSON error message: {send_error}")
                        break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                # Only send error message if WebSocket is still connected
                if client_id in connection_manager.active_connections:
                    try:
                        websocket = connection_manager.active_connections[client_id]
                        if websocket.client_state.value == 1:  # CONNECTED state
                            await connection_manager.send_personal_message({
                                "type": "error",
                                "message": str(e),
                                "timestamp": datetime.utcnow().isoformat()
                            }, client_id)
                    except Exception as send_error:
                        logger.error(f"Failed to send error message: {send_error}")
                        break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connection_manager.disconnect(client_id)

# Background task to send periodic updates
async def send_periodic_updates():
    """Send periodic analytics updates to connected clients"""
    while True:
        try:
            # Only proceed if there are active connections
            if connection_manager.active_connections:
                # Get current metrics
                metrics = await analytics_service.get_real_time_metrics()
                
                if metrics.get("success"):
                    # Broadcast to all connected clients
                    await connection_manager.broadcast({
                        "type": "metrics_update",
                        "metrics": metrics["metrics"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            # Wait 10 seconds before next update
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(30)  # Wait longer on error

# Background task will be started when needed
# asyncio.create_task(send_periodic_updates())