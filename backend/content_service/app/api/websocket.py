import json
import logging
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket_manager import websocket_manager
from app.device_auth import device_auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/device/{device_id}")
async def device_websocket(websocket: WebSocket, device_id: str, token: str = Query(...)):
    """WebSocket endpoint for device connections"""
    try:
        # Verify device token
        payload = device_auth_service.verify_device_jwt(token)
        if not payload or payload.get("sub") != device_id:
            await websocket.close(code=4001, reason="Invalid device token")
            return
        
        # Connect device
        await websocket_manager.connect_device(device_id, websocket)
        
        try:
            while True:
                # Receive messages from device
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    await websocket_manager.handle_device_message(device_id, message)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from device {device_id}: {data}")
                except Exception as e:
                    logger.error(f"Error handling device message from {device_id}: {e}")
                    
        except WebSocketDisconnect:
            logger.info(f"Device {device_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error for device {device_id}: {e}")
        finally:
            await websocket_manager.disconnect_device(device_id)
    
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection for device {device_id}: {e}")
        await websocket.close(code=4000, reason="Connection failed")

@router.websocket("/admin")
async def admin_websocket(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for admin dashboard"""
    try:
        # Verify admin token (you can implement admin token verification here)
        # For now, we'll accept any valid format token
        if not token or len(token) < 10:
            await websocket.close(code=4001, reason="Invalid admin token")
            return
        
        # Connect admin
        await websocket_manager.connect_admin(websocket)
        
        try:
            while True:
                # Admins can send commands to devices
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    await handle_admin_message(message)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from admin: {data}")
                except Exception as e:
                    logger.error(f"Error handling admin message: {e}")
                    
        except WebSocketDisconnect:
            logger.info("Admin dashboard disconnected")
        except Exception as e:
            logger.error(f"WebSocket error for admin: {e}")
        finally:
            await websocket_manager.disconnect_admin(websocket)
    
    except Exception as e:
        logger.error(f"Failed to establish admin WebSocket connection: {e}")
        await websocket.close(code=4000, reason="Connection failed")

async def handle_admin_message(message: Dict):
    """Handle messages from admin dashboard"""
    message_type = message.get("type")
    
    if message_type == "send_to_device":
        device_id = message.get("device_id")
        data = message.get("data")
        if device_id and data:
            await websocket_manager.send_to_device(device_id, data)
    
    elif message_type == "broadcast_to_company":
        company_id = message.get("company_id")
        data = message.get("data")
        if company_id and data:
            await websocket_manager.broadcast_to_devices(company_id, data)
    
    elif message_type == "device_command":
        # Handle specific device commands
        device_id = message.get("device_id")
        command = message.get("command")
        params = message.get("params", {})
        
        if device_id and command:
            command_message = {
                "type": "command",
                "command": command,
                "params": params
            }
            await websocket_manager.send_to_device(device_id, command_message)
    
    else:
        logger.warning(f"Unknown admin message type: {message_type}")

# Startup event to initialize background tasks
@router.on_event("startup")
async def startup_websocket_manager():
    """Start WebSocket manager background tasks"""
    await websocket_manager.start_background_tasks()

@router.on_event("shutdown")
async def shutdown_websocket_manager():
    """Stop WebSocket manager background tasks"""
    await websocket_manager.stop_background_tasks()