"""
Unified Device Management API
Consolidates device-related functionality from:
- app/api/device.py (device registration, authentication, management)
- app/api/screens.py (screen CRUD, layout templates, overlays)
- app/api/simple_screens.py (basic screen listing)

This unified API provides:
- Device registration and authentication
- Screen management (CRUD operations)
- Layout templates and overlays
- Device status monitoring and heartbeats
- QR code generation for registration
- Registration key management
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid
import qrcode
import io
import base64
from PIL import Image
import logging
import secrets
import string

from ..models import (
    DeviceRegistrationCreate, DigitalScreen, ScreenOrientation, ScreenStatus,
    DeviceRegistrationKey, DeviceRegistrationKeyCreate, DeviceHeartbeat, DeviceCapabilities,
    DeviceFingerprint, DeviceType, ScreenCreate, ScreenUpdate, ContentOverlay, ContentOverlayCreate,
    ContentOverlayUpdate, LayoutTemplate, LayoutTemplateCreate, LayoutTemplateUpdate
)
from app.api.auth import require_roles, get_user_company_context
from app.auth_service import get_current_user, get_current_user_with_super_admin_bypass
from ..repo import repo
from ..device_auth import device_auth_service
from ..database_service import db_service
from ..utils.serialization import safe_json_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devices", tags=["devices"])
security = HTTPBearer(auto_error=False)

# ============================================================================
# DEVICE REGISTRATION AND AUTHENTICATION (from app/api/device.py)
# ============================================================================

def generate_secure_key(length: int = 16) -> str:
    """Generate a secure random registration key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"

def convert_objectid_to_str(data):
    """Recursively convert ObjectId instances to strings in a data structure"""
    if isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    else:
        try:
            from bson import ObjectId
            if isinstance(data, ObjectId):
                return str(data)
        except ImportError:
            pass
        return data

@router.post("/keys", response_model=Dict)
async def create_registration_key(
    key_request: DeviceRegistrationKeyCreate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create a new registration key for a company"""
    logger.info(f"Creating registration key for company: {key_request.company_id}")
    try:
        companies = await db_service.list_companies()
        company = next((c for c in companies if c.id == key_request.company_id), None)

        if not company:
            logger.warning(f"Company not found: {key_request.company_id}")
            raise HTTPException(status_code=400, detail="Company not found")

        if company.company_type != "HOST":
            logger.warning(f"Registration key generation denied for non-HOST company: {company.name}")
            raise HTTPException(status_code=400, detail="Registration keys can only be generated for HOST companies")

        key = generate_secure_key()
        key_record = DeviceRegistrationKey(
            id=str(uuid.uuid4()),
            key=key,
            company_id=key_request.company_id,
            created_by="system",
            expires_at=key_request.expires_at or (datetime.utcnow() + timedelta(days=30)),
            used=False,
            used_by_device=None
        )

        await repo.save_device_registration_key(key_record)

        logger.info(f"Generated registration key {key} for company {key_request.company_id}")

        return {
            "success": True,
            "registration_key": key,
            "company_id": key_request.company_id,
            "company_name": company.name,
            "expires_at": key_request.expires_at.isoformat() if key_request.expires_at else None,
            "message": "Registration key generated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate registration key: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate registration key: {str(e)}")

@router.post("/register/enhanced", response_model=Dict)
async def register_device_enhanced(
    device_data: DeviceRegistrationCreate,
    request: Request
):
    """Register a new device with enhanced security features"""
    logger.info(f"Enhanced device registration request: {device_data.device_name}")

    from app.enhanced_device_registration import enhanced_device_registration

    try:
        result = await enhanced_device_registration.register_device_enhanced(device_data, request)
        logger.info(f"Enhanced registration completed for device: {device_data.device_name}")
        return result

    except HTTPException as e:
        logger.warning(f"Enhanced registration blocked: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Enhanced registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhanced registration failed: {str(e)}")

@router.post("/register", response_model=Dict)
async def register_device(
    device_data: DeviceRegistrationCreate,
    request: Request
):
    """Register a new device with enhanced security and authentication"""
    logger.warning("Legacy device registration endpoint used. Consider migrating to /register/enhanced")
    try:
        registration_key_data = await repo.get_device_registration_key(device_data.registration_key)
        if not registration_key_data:
            raise HTTPException(status_code=400, detail="Invalid registration key")

        if registration_key_data.get("used"):
            raise HTTPException(status_code=400, detail="Registration key has already been used")

        expires_at = registration_key_data.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at_dt = datetime.fromisoformat(expires_at)
            else:
                expires_at_dt = expires_at

            if expires_at_dt < datetime.utcnow():
                raise HTTPException(status_code=400, detail="Registration key has expired")

        company_id = registration_key_data.get("company_id")
        if not company_id:
            raise HTTPException(status_code=400, detail="Registration key is not associated with a company")

        companies = await repo.list_companies()
        # Handle both dict and Company object formats
        matching_company = None
        for c in companies:
            if isinstance(c, dict):
                # Check both _id (MongoDB) and id (processed) fields
                if c.get("id") == company_id or c.get("_id") == company_id:
                    matching_company = c
                    break
            else:
                # Assume it's a Company object
                if hasattr(c, 'id') and c.id == company_id:
                    matching_company = c
                    break

        if not matching_company:
            raise HTTPException(status_code=400, detail="Company associated with registration key not found")

        # Extract company name and organization code safely
        if isinstance(matching_company, dict):
            company_name = matching_company.get("name")
            organization_code = matching_company.get("organization_code")
        else:
            # Assume it's a Company object
            company_name = getattr(matching_company, 'name', None)
            organization_code = getattr(matching_company, 'organization_code', None)

        existing_screens = await repo.list_digital_screens(company_id)
        if any(screen.get("name") == device_data.device_name for screen in existing_screens):
            raise HTTPException(status_code=400, detail="Device name already exists for this company")

        client_ip = get_client_ip(request)
        device_id = str(uuid.uuid4())

        capabilities = DeviceCapabilities()
        fingerprint = None

        if hasattr(device_data, 'capabilities') and device_data.capabilities:
            capabilities = device_data.capabilities

        if hasattr(device_data, 'fingerprint') and device_data.fingerprint:
            fingerprint = device_data.fingerprint
        elif client_ip:
            fingerprint = DeviceFingerprint(
                hardware_id=f"hw-{uuid.uuid4().hex[:8]}",
                mac_addresses=[]
            )

        screen_record = DigitalScreen(
            id=device_id,
            name=device_data.device_name,
            description=f"Registered device - {company_name}",
            company_id=company_id,
            location=getattr(device_data, 'location_description', "Device Location (TBD)"),
            resolution_width=capabilities.max_resolution_width if capabilities else 1920,
            resolution_height=capabilities.max_resolution_height if capabilities else 1080,
            orientation=ScreenOrientation.LANDSCAPE,
            aspect_ratio=device_data.aspect_ratio or "16:9",
            registration_key=device_data.registration_key,
            status=ScreenStatus.ACTIVE,
            ip_address=client_ip,
            mac_address=None,
            last_seen=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            device_type=getattr(device_data, 'device_type', DeviceType.KIOSK) if hasattr(DeviceType, '__members__') else DeviceType.KIOSK
        )

        await repo.save_digital_screen(screen_record)

        from app.models import DigitalTwin, DigitalTwinStatus
        digital_twin = DigitalTwin(
            id=str(uuid.uuid4()),
            name=f"Twin-{device_data.device_name}",
            screen_id=device_id,
            company_id=company_id,
            description=f"Digital twin for {device_data.device_name}",
            is_live_mirror=True,
            status=DigitalTwinStatus.STOPPED,
            created_by="system",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        await repo.save_digital_twin(digital_twin)

        auth_result = await device_auth_service.authenticate_device(device_id, company_name or "Unknown Organization")

        await repo.mark_key_used(registration_key_data["id"], device_id)

        logger.info(f"Registered device {device_id} with authentication for company {company_id}")

        return {
            "success": True,
            "device_id": device_id,
            "digital_twin_id": digital_twin.id,
            "message": "Device registered successfully with authentication and digital twin",
            "organization_code": organization_code,
            "company_name": company_name,
            "ip_address": client_ip,
            "certificate": auth_result.get("certificate"),
            "private_key": auth_result.get("private_key"),
            "jwt_token": auth_result.get("jwt_token"),
            "refresh_token": auth_result.get("refresh_token"),
            "token_expires_in": auth_result.get("expires_in"),
            "digital_twin": {
                "id": digital_twin.id,
                "name": digital_twin.name,
                "status": digital_twin.status,
                "is_live_mirror": digital_twin.is_live_mirror
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register device: {str(e)}")

async def verify_device_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify device JWT token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication token required")

    token = credentials.credentials
    payload = device_auth_service.verify_device_jwt(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload

@router.post("/auth/refresh", response_model=Dict)
async def refresh_device_token(request: Dict, current_user: dict = Depends(get_current_user)):
    """Refresh device authentication token"""
    device_id = request.get("device_id")
    refresh_token = request.get("refresh_token")

    if not device_id or not refresh_token:
        raise HTTPException(status_code=400, detail="device_id and refresh_token are required")

    result = await device_auth_service.refresh_device_token(device_id, refresh_token)

    if not result:
        raise HTTPException(status_code=401, detail="Invalid refresh token or device not found")

    return result

@router.post("/heartbeat", response_model=Dict)
async def device_heartbeat(
    heartbeat_data: Dict,
    device_payload: Dict = Depends(verify_device_token)
):
    """Process device heartbeat with health metrics"""
    device_id = device_payload.get("sub")

    if not device_id:
        raise HTTPException(status_code=400, detail="Invalid device token")

    result = await device_auth_service.process_device_heartbeat(device_id, heartbeat_data)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to process heartbeat"))

    return result

@router.post("/enhanced-heartbeat", response_model=Dict)
async def enhanced_device_heartbeat(
    heartbeat_data: Dict,
    device_payload: Dict = Depends(verify_device_token)
):
    """Process enhanced device heartbeat with comprehensive metrics"""
    from ..enhanced_device_analytics import process_enhanced_heartbeat
    
    device_id = device_payload.get("sub")
    if not device_id:
        raise HTTPException(status_code=400, detail="Invalid device token")

    try:
        # Process the enhanced heartbeat data
        result = await process_enhanced_heartbeat(heartbeat_data)
        
        # Also update the digital twin with real-time data
        from ..digital_twins import update_digital_twin_realtime
        await update_digital_twin_realtime(device_id, heartbeat_data)
        
        return {
            "success": True,
            "message": "Enhanced heartbeat processed successfully",
            "digital_twin_updated": True,
            "analytics_recorded": result.get("analytics_recorded", False)
        }
    except Exception as e:
        logging.error(f"Enhanced heartbeat processing failed: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to process enhanced heartbeat: {str(e)}"
        }

@router.get("/heartbeat/{device_id}/history", response_model=Dict)
async def get_device_heartbeat_history(
    device_id: str,
    limit: int = 100,
    device_payload: Dict = Depends(verify_device_token)
):
    """Get device heartbeat history"""
    requesting_device_id = device_payload.get("sub")
    if requesting_device_id != device_id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        heartbeats = await repo.get_device_heartbeats(device_id, limit)
        return convert_objectid_to_str({
            "device_id": device_id,
            "heartbeats": heartbeats,
            "total": len(heartbeats)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get heartbeat history: {str(e)}")

@router.get("/status", response_model=Dict)
async def get_all_devices_status(current_user: dict = Depends(get_current_user)):
    """Get status of all devices accessible to the current user"""
    try:
        # Get all devices accessible to the user
        all_devices = await repo.get_devices()
        
        devices_status = []
        for device in all_devices:
            device_id = device.get("id")
            if not device_id:
                continue
                
            # Get latest heartbeat for this device
            try:
                device_info = await repo.get_device_with_credentials(device_id)
                latest_heartbeat = device_info.get("latest_heartbeat") if device_info else None
                
                is_online = False
                last_seen = None
                if latest_heartbeat:
                    heartbeat_time = latest_heartbeat.get("timestamp")
                    if isinstance(heartbeat_time, str):
                        heartbeat_time = datetime.fromisoformat(heartbeat_time)
                    if heartbeat_time:
                        last_seen = heartbeat_time.isoformat()
                        if (datetime.utcnow() - heartbeat_time).seconds < 300:  # 5 minutes
                            is_online = True
                
                device_status = {
                    "id": device_id,
                    "name": device.get("device_name", "Unknown"),
                    "location": device.get("location", "Unknown"),
                    "status": "online" if is_online else "offline",
                    "is_online": is_online,
                    "last_seen": last_seen,
                    "company_id": device.get("company_id"),
                    "device_type": device.get("device_type", "KIOSK"),
                    "organization_code": device.get("organization_code")
                }
                devices_status.append(device_status)
                
            except Exception as e:
                # If we can't get heartbeat info, still include the device as offline
                device_status = {
                    "id": device_id,
                    "name": device.get("device_name", "Unknown"),
                    "location": device.get("location", "Unknown"),
                    "status": "offline",
                    "is_online": False,
                    "last_seen": None,
                    "company_id": device.get("company_id"),
                    "device_type": device.get("device_type", "KIOSK"),
                    "organization_code": device.get("organization_code")
                }
                devices_status.append(device_status)
        
        return {
            "devices": devices_status,
            "total_devices": len(devices_status),
            "online_devices": len([d for d in devices_status if d["is_online"]]),
            "offline_devices": len([d for d in devices_status if not d["is_online"]])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get devices status: {str(e)}")

@router.get("/status/{device_id}", response_model=Dict)
async def get_device_status(device_id: str, current_user: dict = Depends(get_current_user)):
    """Get enhanced device status with heartbeat and credentials"""
    try:
        device_info = await repo.get_device_with_credentials(device_id)

        if not device_info or not device_info.get("device"):
            raise HTTPException(status_code=404, detail="Device not found")

        device = device_info.get("device")
        credentials = device_info.get("credentials")
        latest_heartbeat = device_info.get("latest_heartbeat")

        is_online = False
        if latest_heartbeat:
            heartbeat_time = latest_heartbeat.get("timestamp")
            if isinstance(heartbeat_time, str):
                heartbeat_time = datetime.fromisoformat(heartbeat_time)
            if heartbeat_time and (datetime.utcnow() - heartbeat_time).seconds < 300:
                is_online = True

        return convert_objectid_to_str({
            **device,
            "is_online": is_online,
            "latest_heartbeat": latest_heartbeat,
            "has_valid_credentials": credentials is not None and not credentials.get("revoked", False),
            "credentials_expires_at": credentials.get("jwt_expires_at") if credentials else None,
            "performance_score": latest_heartbeat.get("performance_score") if latest_heartbeat else None
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get device status: {str(e)}")

@router.get("/generate-qr/{company_id}", response_model=Dict)
async def generate_registration_qr(company_id: str, key_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Generate QR code for device registration"""
    try:
        if not key_id:
            key = generate_secure_key()
            key_record = DeviceRegistrationKey(
                id=str(uuid.uuid4()),
                key=key,
                company_id=company_id,
                created_by="qr-generator",
                expires_at=datetime.utcnow() + timedelta(hours=24),
                used=False,
                used_by_device=None
            )

            await repo.save_device_registration_key(key_record)
            registration_key = key
        else:
            key = generate_secure_key()
            key_record = DeviceRegistrationKey(
                id=str(uuid.uuid4()),
                key=key,
                company_id=company_id,
                created_by="qr-generator",
                expires_at=datetime.utcnow() + timedelta(hours=24),
                used=False,
                used_by_device=None
            )

            await repo.save_device_registration_key(key_record)
            registration_key = key

        companies = await repo.list_companies()
        company = next((c for c in companies if c.get("id") == company_id), None)

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        qr_data = {
            "type": "device_registration",
            "registration_key": registration_key,
            "company_id": company_id,
            "organization_code": company.get("organization_code"),
            "company_name": company.get("name"),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "api_endpoint": "/api/devices/register"
        }

        import json
        qr_json = json.dumps(qr_data)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_json)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

        return {
            "success": True,
            "qr_code_base64": img_base64,
            "qr_data": qr_data,
            "registration_key": registration_key,
            "key_id": key_id,
            "expires_at": qr_data["expires_at"],
            "message": "QR code generated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate QR code: {str(e)}")

@router.get("/keys", response_model=List[Dict])
async def get_registration_keys(current_user: dict = Depends(get_current_user)):
    """Get all registration keys with company information"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.config import settings

        mongo_uri = settings.MONGO_URI
        client = AsyncIOMotorClient(mongo_uri)
        db = client.openkiosk

        keys_collection = db.device_registration_keys
        keys = []
        # Get all keys (both used and unused) for admin view
        async for key_doc in keys_collection.find().sort("created_at", -1):
            if "_id" in key_doc:
                key_doc["_id"] = str(key_doc["_id"])
            keys.append(key_doc)

        companies = await db_service.list_companies()
        company_lookup = {c.id: c for c in companies}

        enhanced_keys = []
        for key in keys:
            company = company_lookup.get(key.get("company_id"))
            if company:
                enhanced_key = {
                    **key,
                    "company_name": company.name,
                    "organization_code": company.organization_code,
                }
                enhanced_keys.append(convert_objectid_to_str(enhanced_key))
            else:
                logger.warning(f"Skipping orphaned registration key {key.get('key')} with invalid company_id {key.get('company_id')}")

        client.close()
        return enhanced_keys

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get registration keys: {str(e)}")

@router.get("/keys/{key_id}", response_model=Dict)
async def get_registration_key_by_id(key_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific registration key by ID with company information"""
    try:
        key = await repo.get_device_registration_key_by_id(key_id)

        if not key:
            raise HTTPException(status_code=404, detail="Registration key not found")

        companies = await repo.list_companies()
        company = next((c for c in companies if c.get("id") == key.get("company_id")), None)

        if not company:
            logger.warning(f"Registration key {key_id} has invalid company_id {key.get('company_id')}")
            raise HTTPException(status_code=404, detail="Registration key has invalid company association")

        enhanced_key = {
            **key,
            "company_name": company.get("name"),
            "organization_code": company.get("organization_code"),
        }

        return convert_objectid_to_str(enhanced_key)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get registration key: {str(e)}")

@router.get("/organization/{org_code}", response_model=Dict)
async def get_devices_by_organization(org_code: str, current_user: dict = Depends(get_current_user)):
    """Get all devices for an organization with enhanced status info"""
    try:
        companies = await repo.list_companies()
        # Check both organization_code and _id fields for MongoDB compatibility
        company = None
        for c in companies:
            if isinstance(c, dict):
                if c.get("organization_code") == org_code:
                    company = c
                    break
            else:
                if hasattr(c, 'organization_code') and c.organization_code == org_code:
                    company = c
                    break

        if not company:
            return {
                "organization_code": org_code,
                "devices": [],
                "total": 0,
                "online": 0,
                "offline": 0
            }

        # Get company ID safely
        company_id = company.get("_id") or company.get("id") if isinstance(company, dict) else getattr(company, 'id', None)
        devices = await repo.list_digital_screens(company_id)

        enhanced_devices = []
        online_count = 0

        for device in devices:
            device_id = device.get("id")
            if not device_id:
                continue

            latest_heartbeat = await repo.get_latest_heartbeat(device_id)

            is_online = False
            if latest_heartbeat:
                heartbeat_time = latest_heartbeat.get("timestamp")
                if isinstance(heartbeat_time, str):
                    heartbeat_time = datetime.fromisoformat(heartbeat_time)
                if heartbeat_time and (datetime.utcnow() - heartbeat_time).seconds < 300:
                    is_online = True
                    online_count += 1

            credentials = await repo.get_device_credentials(device_id)

            enhanced_device = convert_objectid_to_str({
                **device,
                "is_online": is_online,
                "latest_heartbeat": latest_heartbeat,
                "has_valid_credentials": credentials is not None and not credentials.get("revoked", False),
                "performance_score": latest_heartbeat.get("performance_score") if latest_heartbeat else None
            })
            enhanced_devices.append(enhanced_device)

        return convert_objectid_to_str({
            "organization_code": org_code,
            "company_name": company.get("name"),
            "devices": enhanced_devices,
            "total": len(devices),
            "online": online_count,
            "offline": len(devices) - online_count
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organization devices: {str(e)}")

@router.get("/registration/stats", response_model=Dict)
async def get_registration_statistics(current_user: dict = Depends(get_current_user)):
    """Get device registration statistics and security metrics"""
    try:
        from app.enhanced_device_registration import enhanced_device_registration
        stats = await enhanced_device_registration.get_registration_stats()

        total_devices = len(await repo.list_digital_screens())
        total_registration_keys = len(await repo.list_device_registration_keys())

        stats.update({
            "total_registered_devices": total_devices,
            "total_registration_keys_issued": total_registration_keys
        })

        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting registration stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/security/status", response_model=Dict)
async def get_device_security_status(current_user: dict = Depends(get_current_user)):
    """Get device security status and monitoring information"""
    try:
        from app.enhanced_device_registration import enhanced_device_registration
        registration_stats = await enhanced_device_registration.get_registration_stats()

        all_devices = await repo.list_digital_screens()
        device_status_counts = {}
        for device in all_devices:
            status = device.get("status", "unknown")
            device_status_counts[status] = device_status_counts.get(status, 0) + 1

        recent_failures = registration_stats["failed_registrations"]
        blocked_ips = registration_stats["blocked_ip_addresses"]

        security_level = "normal"
        if blocked_ips > 0 or recent_failures > 10:
            security_level = "elevated"
        if blocked_ips > 5 or recent_failures > 50:
            security_level = "high"

        return {
            "success": True,
            "security_status": {
                "level": security_level,
                "blocked_ip_count": blocked_ips,
                "recent_failed_attempts": recent_failures,
                "device_status_breakdown": device_status_counts,
                "total_monitored_ips": registration_stats["active_monitoring_ips"],
                "last_updated": registration_stats["timestamp"]
            }
        }

    except Exception as e:
        logger.error(f"Error getting security status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get security status: {str(e)}")

@router.post("/registration/unblock-ip", response_model=Dict)
async def unblock_ip_address(request_data: Dict, current_user: dict = Depends(get_current_user)):
    """Unblock an IP address that was blocked for suspicious activity"""
    try:
        from app.enhanced_device_registration import enhanced_device_registration

        ip_address = request_data.get("ip_address")
        if not ip_address:
            raise HTTPException(status_code=400, detail="IP address is required")

        success = await enhanced_device_registration.unblock_ip(ip_address)

        if success:
            logger.info(f"Manually unblocked IP address: {ip_address}")
            return {"message": f"Successfully unblocked IP {ip_address}", "success": True}
        else:
            return {"message": f"IP {ip_address} was not blocked", "success": False}

    except Exception as e:
        logger.error(f"Error unblocking IP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to unblock IP: {str(e)}")

@router.delete("/keys/cleanup", response_model=Dict)
async def cleanup_orphaned_keys(current_user: dict = Depends(get_current_user)):
    """Clean up registration keys with invalid company associations"""
    try:
        keys = await repo.list_device_registration_keys()
        companies = await repo.list_companies()

        company_ids = {c.get("id") for c in companies}

        orphaned_keys = []
        for key in keys:
            company_id = key.get("company_id")
            if company_id not in company_ids:
                orphaned_keys.append(key)

        deleted_count = 0
        for key in orphaned_keys:
            await repo.delete_device_registration_key(key.get("id"))
            deleted_count += 1
            logger.info(f"Deleted orphaned registration key {key.get('key')} with invalid company_id {key.get('company_id')}")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} orphaned registration keys"
        }

    except Exception as e:
        logger.error(f"Failed to cleanup orphaned keys: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup orphaned keys: {str(e)}")

# ============================================================================
# SCREEN MANAGEMENT (from app/api/screens.py and app/api/simple_screens.py)
# ============================================================================

@router.get("/", response_model=List[dict])
async def list_devices(
    company_id: Optional[str] = None,
    status: Optional[ScreenStatus] = None,
    current_user: dict = Depends(get_current_user_with_super_admin_bypass),
    company_context=Depends(get_user_company_context)
):
    """List all devices with company-scoped filtering"""
    if current_user.get("user_type") == "SUPER_USER":
        devices = await repo.list_digital_screens(company_id)
        if status:
            devices = [s for s in devices if s.get("status") == status.value]
        return devices

    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}

    devices = await repo.list_digital_screens(company_id)

    if status:
        devices = [s for s in devices if s.get("status") == status.value]

    if not is_platform_admin:
        devices = [s for s in devices if s.get("company_id") in accessible_company_ids]

    return devices

@router.post("/", response_model=dict)
async def create_device(
    device_data: ScreenCreate,
    current_user: dict = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new digital screen/device"""

    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}

    if not is_platform_admin and device_data.company_id not in accessible_company_ids:
        raise HTTPException(status_code=403, detail="Access denied to create devices for this company")

    current_user_id = current_user.get("id")
    user_can_create = is_platform_admin

    if not is_platform_admin:
        user_role = await repo.get_user_role_in_company(current_user_id, device_data.company_id)
        if user_role:
            role_details = user_role.get("role_details", {})
            company_role_type = role_details.get("company_role_type")
            if company_role_type in ["COMPANY_ADMIN", "EDITOR"]:
                user_can_create = True

    if not user_can_create:
        raise HTTPException(status_code=403, detail="Access denied: Only company admins and editors can create devices")

    device_id = str(uuid.uuid4())
    device = device_data.model_dump()
    device.update({
        "id": device_id,
        "status": ScreenStatus.ACTIVE,
        "last_seen": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    from app.models import DigitalScreen
    device_model = DigitalScreen(**device)
    result = await repo.save_digital_screen(device_model)
    return result

@router.get("/{device_id}", response_model=dict)
async def get_device(
    device_id: str,
    current_user: dict = Depends(get_current_user_with_super_admin_bypass),
    company_context=Depends(get_user_company_context)
):
    """Get a specific digital screen/device"""
    if current_user.get("user_type") == "SUPER_USER":
        device = await repo.get_digital_screen(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return device

    device = await repo.get_digital_screen(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}

    if not is_platform_admin:
        if device.get("company_id") not in accessible_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this device")

    return device

@router.put("/{device_id}", response_model=dict)
async def update_device(
    device_id: str,
    device_data: ScreenUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a digital screen/device"""
    device = await repo.get_digital_screen(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)

    if not user_is_admin and not user_has_global_access:
        user_company_ids = [role.get("company_id") for role in user_roles]
        if device.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this device")

    update_data = device_data.model_dump(exclude_unset=True)
    success = await repo.update_digital_screen(device_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update device")

    updated_device = await repo.get_digital_screen(device_id)
    return updated_device

@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a digital screen/device"""
    device = await repo.get_digital_screen(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)

    if not user_is_admin and not user_has_global_access:
        user_company_ids = [role.get("company_id") for role in user_roles]
        if device.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this device")

    success = await repo.delete_digital_screen(device_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete device")

    return {"message": "Device deleted successfully"}

# ============================================================================
# LAYOUT TEMPLATES (from app/api/screens.py)
# ============================================================================

@router.get("/templates", response_model=List[dict])
async def get_layout_templates(
    is_public: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get layout templates with company-scoped access"""
    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}

    if is_platform_admin:
        templates = await repo.list_layout_templates(is_public=is_public)
    else:
        all_templates = []
        for company_id in accessible_company_ids:
            company_templates = await repo.list_layout_templates(company_id=company_id, is_public=is_public)
            all_templates.extend(company_templates)

        seen_ids = set()
        templates = []
        for template in all_templates:
            if template.get("id") not in seen_ids:
                seen_ids.add(template.get("id"))
                templates.append(template)

    return templates

@router.post("/templates", response_model=dict)
async def create_layout_template(
    template_data: LayoutTemplateCreate,
    current_user: dict = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new layout template"""
    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}

    if not is_platform_admin and template_data.company_id not in accessible_company_ids:
        raise HTTPException(status_code=403, detail="Access denied to create templates for this company")

    template_dict = template_data.model_dump()
    template_dict.update({
        "id": str(uuid.uuid4()),
        "created_by": current_user.get("id"),
        "usage_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    result = await repo.save_layout_template(template_dict)
    return result

@router.get("/templates/{template_id}", response_model=dict)
async def get_layout_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get a specific layout template"""
    template = await repo.get_layout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Layout template not found")

    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}

    if not is_platform_admin:
        if not template.get("is_public") and template.get("company_id") not in accessible_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this template")

    return template

@router.put("/templates/{template_id}", response_model=dict)
async def update_layout_template(
    template_id: str,
    template_data: LayoutTemplateUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a layout template"""
    template = await repo.get_layout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Layout template not found")

    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)

    if not user_is_admin and not user_has_global_access:
        user_company_ids = [role.get("company_id") for role in user_roles]
        if template.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to modify this template")

    update_data = template_data.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    success = await repo.update_layout_template(template_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update template")

    updated_template = await repo.get_layout_template(template_id)
    return updated_template

@router.delete("/templates/{template_id}")
async def delete_layout_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a layout template"""
    template = await repo.get_layout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Layout template not found")

    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)

    if not user_is_admin and not user_has_global_access:
        user_company_ids = [role.get("company_id") for role in user_roles]
        if template.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to delete this template")

    success = await repo.delete_layout_template(template_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete template")

    return {"message": "Layout template deleted successfully"}

@router.post("/templates/{template_id}/use")
async def use_layout_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Increment usage count when template is used"""
    template = await repo.get_layout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Layout template not found")

    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)

    if not user_is_admin and not user_has_global_access:
        user_company_ids = [role.get("company_id") for role in user_roles]
        if template.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to use this template")

    success = await repo.increment_template_usage(template_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update template usage")

    return {"message": "Template usage recorded"}

# ============================================================================
# DEVICE CONTENT MANAGEMENT (from app/api/device.py)
# ============================================================================

@router.get("/content/pull/{device_id}")
async def pull_device_content(
    device_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user)
):
    """Pull content for a specific device based on its company and permissions"""
    try:
        if not credentials:
            raise HTTPException(status_code=401, detail="Device authentication required")

        device_token = credentials.credentials
        device = await device_auth_service.authenticate_device(device_id, device_token)

        if not device:
            raise HTTPException(status_code=401, detail="Invalid device credentials")

        device_company_id = device.get("company_id")
        if not device_company_id:
            raise HTTPException(status_code=400, detail="Device not associated with a company")

        companies = await repo.list_companies()
        device_company = next((c for c in companies if c.get("id") == device_company_id), None)

        if not device_company:
            raise HTTPException(status_code=404, detail="Device company not found")

        accessible_content = []

        if device_company.get("company_type") == "HOST":
            own_content = await repo.get_content_by_company(device_company_id, status="approved")
            accessible_content.extend(own_content)

            if device_company.get("sharing_settings", {}).get("allow_content_sharing", True):
                shared_content = await repo.get_shared_content_for_company(device_company_id)
                accessible_content.extend(shared_content)

        elif device_company.get("company_type") == "ADVERTISER":
            own_content = await repo.get_content_by_company(device_company_id, status="approved")
            accessible_content = own_content

        await repo.update_device_last_seen(device_id, datetime.utcnow())

        return {
            "success": True,
            "device_id": device_id,
            "company_id": device_company_id,
            "company_type": device_company.get("company_type"),
            "content_count": len(accessible_content),
            "content": [convert_objectid_to_str(content) for content in accessible_content],
            "last_updated": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pull content for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve device content")

@router.post("/heartbeat/{device_id}")
async def device_heartbeat(
    device_id: str,
    heartbeat_data: DeviceHeartbeat,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user)
):
    """Device health check and status reporting endpoint"""
    try:
        if not credentials:
            raise HTTPException(status_code=401, detail="Device authentication required")

        device_token = credentials.credentials
        device = await device_auth_service.authenticate_device(device_id, device_token)

        if not device:
            raise HTTPException(status_code=401, detail="Invalid device credentials")

        status_update = {
            "last_heartbeat": datetime.utcnow(),
            "status": "active",
            "health_data": {
                "cpu_usage": heartbeat_data.cpu_usage,
                "memory_usage": heartbeat_data.memory_usage,
                "disk_usage": heartbeat_data.disk_usage,
                "network_status": heartbeat_data.network_status,
                "display_status": heartbeat_data.display_status,
                "current_content": heartbeat_data.current_content_id,
                "performance_score": heartbeat_data.performance_score,
                "errors": heartbeat_data.errors or []
            }
        }

        await repo.update_device_status(device_id, status_update)

        pending_commands = await repo.get_device_pending_commands(device_id)

        return {
            "success": True,
            "device_id": device_id,
            "status": "acknowledged",
            "server_time": datetime.utcnow().isoformat(),
            "pending_commands": pending_commands,
            "next_heartbeat_seconds": 300
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Device heartbeat failed for {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Heartbeat processing failed")

@router.post("/analytics/{device_id}")
async def report_device_analytics(
    device_id: str,
    analytics_data: Dict,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: dict = Depends(get_current_user)
):
    """Device analytics reporting endpoint"""
    try:
        if not credentials:
            raise HTTPException(status_code=401, detail="Device authentication required")

        device_token = credentials.credentials
        device = await device_auth_service.authenticate_device(device_id, device_token)

        if not device:
            raise HTTPException(status_code=401, detail="Invalid device credentials")

        analytics_record = {
            "device_id": device_id,
            "company_id": device.get("company_id"),
            "timestamp": datetime.utcnow(),
            "analytics_data": analytics_data,
            "data_type": "device_analytics"
        }

        await repo.store_device_analytics(analytics_record)

        return {
            "success": True,
            "device_id": device_id,
            "message": "Analytics data recorded successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics reporting failed for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Analytics reporting failed")
