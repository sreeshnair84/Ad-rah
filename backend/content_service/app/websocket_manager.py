import json
import logging
import asyncio
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
from app.repo import repo
from app.device_auth import device_auth_service

logger = logging.getLogger(__name__)

class DeviceWebSocketManager:
    """Manages WebSocket connections for real-time device communication"""
    
    def __init__(self):
        # Active WebSocket connections
        self.device_connections: Dict[str, WebSocket] = {}  # device_id -> websocket
        self.admin_connections: Set[WebSocket] = set()  # Admin dashboard connections
        
        # Message queues for offline devices
        self.device_message_queues: Dict[str, List[Dict]] = {}
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._cleanup_old_messages())
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._monitor_device_heartbeats())
    
    async def stop_background_tasks(self):
        """Stop background tasks"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.cleanup_task = None
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            self.heartbeat_task = None
    
    async def connect_device(self, device_id: str, websocket: WebSocket):
        """Connect a device WebSocket"""
        await websocket.accept()
        self.device_connections[device_id] = websocket
        
        logger.info(f"Device {device_id} connected via WebSocket")
        
        # Send any queued messages
        if device_id in self.device_message_queues:
            for message in self.device_message_queues[device_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send queued message to device {device_id}: {e}")
            
            # Clear the queue
            del self.device_message_queues[device_id]
        
        # Notify admins about device connection
        await self._broadcast_to_admins({
            "type": "device_connected",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def disconnect_device(self, device_id: str):
        """Disconnect a device WebSocket"""
        if device_id in self.device_connections:
            del self.device_connections[device_id]
            logger.info(f"Device {device_id} disconnected from WebSocket")
            
            # Notify admins about device disconnection
            await self._broadcast_to_admins({
                "type": "device_disconnected",
                "device_id": device_id,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def connect_admin(self, websocket: WebSocket):
        """Connect an admin dashboard WebSocket"""
        await websocket.accept()
        self.admin_connections.add(websocket)
        logger.info("Admin dashboard connected via WebSocket")
        
        # Send current device status summary
        await self._send_device_status_summary(websocket)
    
    async def disconnect_admin(self, websocket: WebSocket):
        """Disconnect an admin WebSocket"""
        self.admin_connections.discard(websocket)
        logger.info("Admin dashboard disconnected from WebSocket")
    
    async def send_to_device(self, device_id: str, message: Dict) -> bool:
        """Send a message to a specific device"""
        message["timestamp"] = datetime.utcnow().isoformat()
        
        if device_id in self.device_connections:
            try:
                websocket = self.device_connections[device_id]
                await websocket.send_text(json.dumps(message))
                return True
            except Exception as e:
                logger.error(f"Failed to send message to device {device_id}: {e}")
                # Remove dead connection
                await self.disconnect_device(device_id)
        
        # Queue message for when device comes online
        if device_id not in self.device_message_queues:
            self.device_message_queues[device_id] = []
        
        self.device_message_queues[device_id].append(message)
        logger.info(f"Queued message for offline device {device_id}")
        return False
    
    async def broadcast_to_devices(self, company_id: str, message: Dict):
        """Broadcast a message to all devices of a company"""
        try:
            devices = await repo.list_digital_screens(company_id)
            sent_count = 0
            
            for device in devices:
                device_id = device.get("id")
                if device_id:
                    success = await self.send_to_device(device_id, message)
                    if success:
                        sent_count += 1
            
            logger.info(f"Broadcasted message to {sent_count} devices in company {company_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast to company {company_id}: {e}")
    
    async def handle_device_message(self, device_id: str, message: Dict):
        """Handle incoming message from device"""
        message_type = message.get("type")
        
        if message_type == "heartbeat":
            # Process heartbeat data
            await self._handle_device_heartbeat(device_id, message.get("data", {}))
        elif message_type == "content_status":
            # Handle content playback status updates
            await self._handle_content_status(device_id, message.get("data", {}))
        elif message_type == "error":
            # Handle error reports
            await self._handle_device_error(device_id, message.get("data", {}))
        else:
            logger.warning(f"Unknown message type from device {device_id}: {message_type}")
    
    async def _handle_device_heartbeat(self, device_id: str, heartbeat_data: Dict):
        """Process device heartbeat via WebSocket"""
        try:
            # Use existing heartbeat processing
            result = await device_auth_service.process_device_heartbeat(device_id, heartbeat_data)
            
            if result.get("success"):
                # Broadcast heartbeat update to admins
                await self._broadcast_to_admins({
                    "type": "device_heartbeat",
                    "device_id": device_id,
                    "data": heartbeat_data,
                    "performance_score": result.get("performance_score"),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Failed to process WebSocket heartbeat from device {device_id}: {e}")
    
    async def _handle_content_status(self, device_id: str, status_data: Dict):
        """Handle content playback status updates"""
        try:
            # Broadcast to admins
            await self._broadcast_to_admins({
                "type": "content_status",
                "device_id": device_id,
                "data": status_data,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Content status update from device {device_id}: {status_data.get('status')}")
        except Exception as e:
            logger.error(f"Failed to handle content status from device {device_id}: {e}")
    
    async def _handle_device_error(self, device_id: str, error_data: Dict):
        """Handle device error reports"""
        try:
            # Log the error
            logger.error(f"Device {device_id} reported error: {error_data}")
            
            # Broadcast to admins
            await self._broadcast_to_admins({
                "type": "device_error",
                "device_id": device_id,
                "data": error_data,
                "timestamp": datetime.utcnow().isoformat(),
                "severity": error_data.get("severity", "warning")
            })
            
        except Exception as e:
            logger.error(f"Failed to handle device error from {device_id}: {e}")
    
    async def _broadcast_to_admins(self, message: Dict):
        """Broadcast message to all admin connections"""
        if not self.admin_connections:
            return
        
        dead_connections = []
        message_text = json.dumps(message)
        
        for websocket in self.admin_connections:
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.error(f"Failed to send to admin connection: {e}")
                dead_connections.append(websocket)
        
        # Remove dead connections
        for websocket in dead_connections:
            self.admin_connections.discard(websocket)
    
    async def _send_device_status_summary(self, websocket: WebSocket):
        """Send current device status summary to new admin connection"""
        try:
            # Get all companies and their devices
            companies = await repo.list_companies()
            device_summary = []
            
            for company in companies:
                company_id = company.get("id")
                devices = await repo.list_digital_screens(company_id)
                
                for device in devices:
                    device_id = device.get("id")
                    
                    # Get latest heartbeat
                    latest_heartbeat = await repo.get_latest_heartbeat(device_id)
                    
                    # Check online status
                    is_online = device_id in self.device_connections
                    
                    device_summary.append({
                        "device_id": device_id,
                        "name": device.get("name"),
                        "company_name": company.get("name"),
                        "is_online": is_online,
                        "latest_heartbeat": latest_heartbeat,
                        "performance_score": latest_heartbeat.get("performance_score") if latest_heartbeat else None
                    })
            
            await websocket.send_text(json.dumps({
                "type": "device_status_summary",
                "data": device_summary,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Failed to send device status summary: {e}")
    
    async def _cleanup_old_messages(self):
        """Background task to cleanup old queued messages"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                for device_id in list(self.device_message_queues.keys()):
                    messages = self.device_message_queues[device_id]
                    
                    # Remove messages older than 24 hours
                    filtered_messages = []
                    for msg in messages:
                        msg_time_str = msg.get("timestamp")
                        if msg_time_str:
                            msg_time = datetime.fromisoformat(msg_time_str.replace("Z", "+00:00"))
                            if msg_time > cutoff_time:
                                filtered_messages.append(msg)
                    
                    if filtered_messages:
                        self.device_message_queues[device_id] = filtered_messages
                    else:
                        del self.device_message_queues[device_id]
                
                logger.info(f"Cleaned up old messages. Active queues: {len(self.device_message_queues)}")
                
            except Exception as e:
                logger.error(f"Error in message cleanup task: {e}")
    
    async def _monitor_device_heartbeats(self):
        """Background task to monitor device heartbeat health"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Get all devices
                companies = await repo.list_companies()
                offline_devices = []
                
                for company in companies:
                    devices = await repo.list_digital_screens(company.get("id"))
                    
                    for device in devices:
                        device_id = device.get("id")
                        
                        # Check if device is connected
                        is_connected = device_id in self.device_connections
                        
                        # Check last heartbeat time
                        latest_heartbeat = await repo.get_latest_heartbeat(device_id)
                        
                        if not is_connected or not latest_heartbeat:
                            offline_devices.append({
                                "device_id": device_id,
                                "name": device.get("name"),
                                "company_name": company.get("name"),
                                "last_seen": device.get("last_seen")
                            })
                
                if offline_devices:
                    # Broadcast offline device alert
                    await self._broadcast_to_admins({
                        "type": "offline_devices_alert",
                        "data": offline_devices,
                        "count": len(offline_devices),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                logger.info(f"Heartbeat monitor: {len(offline_devices)} devices offline")
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor task: {e}")

# Global WebSocket manager instance
websocket_manager = DeviceWebSocketManager()