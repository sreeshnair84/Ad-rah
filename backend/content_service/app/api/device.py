from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional, List
from datetime import datetime
import uuid
import qrcode
import io
import base64
from PIL import Image
import logging

from app.models import (
    DeviceRegistrationCreate, DigitalScreen, ScreenOrientation, ScreenStatus, 
    DeviceRegistrationKey, DeviceRegistrationKeyCreate, DeviceHeartbeat, DeviceCapabilities, 
    DeviceFingerprint, DeviceType
)
from app.repo import repo
from app.device_auth import device_auth_service
from app.database_service import db_service
# from app.enhanced_device_registration import enhanced_device_registration
import secrets
import string
from datetime import timedelta

# Configure logger
logger = logging.getLogger(__name__)

def convert_objectid_to_str(data):
    """Recursively convert ObjectId instances to strings in a data structure"""
    if isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    else:
        # Try to convert ObjectId to string, fallback to original data
        try:
            from bson import ObjectId
            if isinstance(data, ObjectId):
                return str(data)
        except ImportError:
            pass
        return data

router = APIRouter(prefix="/device", tags=["device"])
security = HTTPBearer(auto_error=False)

@router.get("/")
async def list_devices():
    """List all devices - basic endpoint for testing"""
    try:
        devices = await repo.list_digital_screens()
        return {"devices": devices, "count": len(devices)}
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        return {"devices": [], "count": 0, "error": str(e)}

# Helper function to generate secure registration key
def generate_secure_key(length: int = 16) -> str:
    """Generate a secure random registration key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Helper function to get client IP
def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers first (for proxy/load balancer scenarios)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for other proxy headers
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"

# Helper function to get MAC address (this is a placeholder - actual MAC detection would require system calls)
def get_client_mac() -> Optional[str]:
    """Get client MAC address (placeholder - would need system-level access)"""
    # In a real implementation, this would require accessing network interfaces
    # For now, we'll return None and let the device provide it if available
    return None



@router.post("/keys", response_model=Dict)
async def create_registration_key(
    key_request: DeviceRegistrationKeyCreate,
    request: Request
):
    """Create a new registration key for a company"""
    logger.info(f"Creating registration key for company: {key_request.company_id}")
    try:
        # Verify the company exists and is a HOST company using db_service
        companies = await db_service.list_companies()
        company = next((c for c in companies if c.id == key_request.company_id), None)
        
        if not company:
            logger.warning(f"Company not found: {key_request.company_id}")
            raise HTTPException(
                status_code=400,
                detail="Company not found"
            )
        
        # Only HOST companies can generate registration keys for devices
        if company.company_type != "HOST":
            logger.warning(f"Registration key generation denied for non-HOST company: {company.name} (type: {company.company_type})")
            raise HTTPException(
                status_code=400,
                detail="Registration keys can only be generated for HOST companies"
            )

        # Generate a secure registration key
        key = generate_secure_key()
        
        # Create the registration key record
        key_record = DeviceRegistrationKey(
            id=str(uuid.uuid4()),
            key=key,
            company_id=key_request.company_id,
            created_by="system",  # TODO: Get from authenticated user
            expires_at=key_request.expires_at or (datetime.utcnow() + timedelta(days=30)),  # Default 30 days
            used=False,
            used_by_device=None
        )
        
        # Save to database
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate registration key: {str(e)}"
        )


@router.post("/generate-key", response_model=Dict)
async def generate_registration_key(
    key_request: DeviceRegistrationKeyCreate,
    request: Request
):
    """Generate a new registration key for a company (legacy endpoint)"""
    return await create_registration_key(key_request, request)


@router.post("/register/enhanced", response_model=Dict)
async def register_device_enhanced(
    device_data: DeviceRegistrationCreate,
    request: Request
):
    """Register a new device with enhanced security, rate limiting, and comprehensive validation"""
    return await enhanced_device_registration.register_device_enhanced(device_data, request)


@router.post("/register", response_model=Dict)
async def register_device(
    device_data: DeviceRegistrationCreate,
    request: Request
):
    """Register a new device with enhanced security and authentication (Legacy endpoint - use /register/enhanced instead)"""
    logger.warning("Legacy device registration endpoint used. Consider migrating to /register/enhanced")
    try:
        # Validate registration key
        registration_key_data = await repo.get_device_registration_key(device_data.registration_key)
        if not registration_key_data:
            raise HTTPException(
                status_code=400,
                detail="Invalid registration key"
            )
        
        # Check if key is already used
        if registration_key_data.get("used"):
            raise HTTPException(
                status_code=400,
                detail="Registration key has already been used"
            )
        
        # Check if key has expired
        expires_at = registration_key_data.get("expires_at")
        if expires_at:
            # Handle both string and datetime objects
            if isinstance(expires_at, str):
                expires_at_dt = datetime.fromisoformat(expires_at)
            else:
                expires_at_dt = expires_at
            
            if expires_at_dt < datetime.utcnow():
                raise HTTPException(
                    status_code=400,
                    detail="Registration key has expired"
                )
        
        # Get company from the registration key
        company_id = registration_key_data.get("company_id")
        if not company_id:
            raise HTTPException(
                status_code=400,
                detail="Registration key is not associated with a company"
            )
        
        companies = await repo.list_companies()
        matching_company = next((c for c in companies if c.get("id") == company_id), None)
        
        if not matching_company:
            raise HTTPException(
                status_code=400,
                detail="Company associated with registration key not found"
            )

        # Check if device name already exists for this company
        existing_screens = await repo.list_digital_screens(company_id)
        if any(screen.get("name") == device_data.device_name for screen in existing_screens):
            raise HTTPException(
                status_code=400,
                detail="Device name already exists for this company"
            )

        # Get client IP and enhanced device info
        client_ip = get_client_ip(request)
        client_mac = get_client_mac()
        device_id = str(uuid.uuid4())
        
        # Extract device capabilities and fingerprint from request if provided
        capabilities = DeviceCapabilities()
        fingerprint = None
        
        if hasattr(device_data, 'capabilities') and device_data.capabilities:
            capabilities = device_data.capabilities
            
        if hasattr(device_data, 'fingerprint') and device_data.fingerprint:
            fingerprint = device_data.fingerprint
        elif client_mac:
            # Create basic fingerprint from available info
            fingerprint = DeviceFingerprint(
                hardware_id=f"hw-{uuid.uuid4().hex[:8]}",
                mac_addresses=[client_mac] if client_mac else []
            )
        
        # Create enhanced DigitalScreen record
        screen_record = DigitalScreen(
            id=device_id,
            name=device_data.device_name,
            description=f"Registered device - {matching_company.get('name')}",
            company_id=company_id,
            location=getattr(device_data, 'location_description', "Device Location (TBD)"),
            resolution_width=capabilities.max_resolution_width,
            resolution_height=capabilities.max_resolution_height,
            orientation=ScreenOrientation.LANDSCAPE,
            aspect_ratio=device_data.aspect_ratio or "16:9",
            registration_key=device_data.registration_key,
            status=ScreenStatus.ACTIVE,
            ip_address=client_ip,
            mac_address=client_mac,
            last_seen=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            # Enhanced fields
            device_type=getattr(device_data, 'device_type', DeviceType.KIOSK),
            capabilities=capabilities.model_dump() if capabilities else None,
            fingerprint=fingerprint.model_dump() if fingerprint else None
        )
        
        # Save device to database
        await repo.save_digital_screen(screen_record)
        
        # Create associated digital twin for the device
        from app.models import DigitalTwin, DigitalTwinStatus
        digital_twin = DigitalTwin(
            id=str(uuid.uuid4()),
            name=f"Twin-{device_data.device_name}",
            screen_id=device_id,
            company_id=company_id,
            description=f"Digital twin for {device_data.device_name}",
            is_live_mirror=True,  # Enable live mirroring by default
            status=DigitalTwinStatus.STOPPED,
            created_by="system",  # TODO: Get from authenticated user context
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save digital twin to database
        await repo.save_digital_twin(digital_twin)
        
        # Generate device authentication credentials
        auth_result = await device_auth_service.authenticate_device(
            device_id, 
            matching_company.get('name')
        )
        
        # Mark the registration key as used
        await repo.mark_key_used(registration_key_data["id"], device_id)
        
        logger.info(f"Registered device {device_id} with authentication for company {company_id}")

        return {
            "success": True,
            "device_id": device_id,
            "digital_twin_id": digital_twin.id,
            "message": "Device registered successfully with authentication and digital twin",
            "organization_code": device_data.organization_code,
            "company_name": matching_company.get("name"),
            "ip_address": client_ip,
            "mac_address": client_mac,
            # Authentication credentials
            "certificate": auth_result.get("certificate"),
            "private_key": auth_result.get("private_key"),  # Only provided once
            "jwt_token": auth_result.get("jwt_token"),
            "refresh_token": auth_result.get("refresh_token"),
            "token_expires_in": auth_result.get("expires_in"),
            # Digital twin information
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register device: {str(e)}"
        )


# Device authentication middleware
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
async def refresh_device_token(request: Dict):
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
    device_id = device_payload.get("sub")  # Device ID from JWT
    
    if not device_id:
        raise HTTPException(status_code=400, detail="Invalid device token")
    
    result = await device_auth_service.process_device_heartbeat(device_id, heartbeat_data)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to process heartbeat"))
    
    return result


@router.get("/heartbeat/{device_id}/history", response_model=Dict)
async def get_device_heartbeat_history(
    device_id: str,
    limit: int = 100,
    device_payload: Dict = Depends(verify_device_token)
):
    """Get device heartbeat history"""
    # Verify the requesting device can access this data
    requesting_device_id = device_payload.get("sub")
    if requesting_device_id != device_id:
        # Only allow access to own heartbeat data, or admin access
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


@router.get("/status/{device_id}", response_model=Dict)
async def get_device_status(device_id: str):
    """Get enhanced device status with heartbeat and credentials"""
    try:
        device_info = await repo.get_device_with_credentials(device_id)
        
        if not device_info or not device_info.get("device"):
            raise HTTPException(status_code=404, detail="Device not found")
        
        device = device_info.get("device")
        credentials = device_info.get("credentials")
        latest_heartbeat = device_info.get("latest_heartbeat")
        
        # Determine online status (heartbeat within last 5 minutes)
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
async def generate_registration_qr(company_id: str, key_id: Optional[str] = None):
    """Generate QR code for device registration"""
    try:
        # If no key_id provided, create a new registration key
        if not key_id:
            # Create a temporary registration key
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
            key_id = key_record.id
            registration_key = key
        else:
            # Use existing key - need to implement get_device_registration_key_by_id
            # For now, create new key
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
        
        # Get company info
        companies = await repo.list_companies()
        company = next((c for c in companies if c.get("id") == company_id), None)
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Create QR code data
        qr_data = {
            "type": "device_registration",
            "registration_key": registration_key,
            "company_id": company_id,
            "organization_code": company.get("organization_code"),
            "company_name": company.get("name"),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "api_endpoint": "/api/device/register"
        }
        
        # Convert to JSON string for QR code
        import json
        qr_json = json.dumps(qr_data)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_json)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for API response
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate QR code: {str(e)}"
        )


@router.get("/keys", response_model=List[Dict])
async def get_registration_keys():
    """Get all registration keys with company information"""
    try:
        # Connect to MongoDB directly to get registration keys
        from motor.motor_asyncio import AsyncIOMotorClient
        from app.config import settings
        
        mongo_uri = settings.MONGO_URI
        client = AsyncIOMotorClient(mongo_uri)
        db = client.openkiosk
        
        # Get all registration keys directly from MongoDB
        keys_collection = db.device_registration_keys
        keys = []
        async for key_doc in keys_collection.find():
            # Convert ObjectIds to strings
            if "_id" in key_doc:
                key_doc["_id"] = str(key_doc["_id"])
            keys.append(key_doc)
        
        # Get all companies for lookup using db_service
        companies = await db_service.list_companies()
        company_lookup = {c.id: c for c in companies}
        
        # Enhance keys with company information, skipping orphaned keys
        enhanced_keys = []
        for key in keys:
            company = company_lookup.get(key.get("company_id"))
            if company:  # Only include keys with valid company associations
                enhanced_key = {
                    **key,
                    "company_name": company.name,
                    "organization_code": company.organization_code,
                }
                enhanced_keys.append(convert_objectid_to_str(enhanced_key))
            else:
                # Log orphaned key for monitoring
                logger.warning(f"Skipping orphaned registration key {key.get('key')} with invalid company_id {key.get('company_id')}")
        
        client.close()
        return enhanced_keys
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get registration keys: {str(e)}"
        )


@router.get("/keys/{key_id}", response_model=Dict)
async def get_registration_key_by_id(key_id: str):
    """Get a specific registration key by ID with company information"""
    try:
        # Get the specific registration key
        key = await repo.get_device_registration_key_by_id(key_id)
        
        if not key:
            raise HTTPException(
                status_code=404,
                detail="Registration key not found"
            )
        
        # Get company information
        companies = await repo.list_companies()
        company = next((c for c in companies if c.get("id") == key.get("company_id")), None)
        
        if not company:
            # Key has invalid company_id - return 404 as the key is effectively orphaned
            logger.warning(f"Registration key {key_id} has invalid company_id {key.get('company_id')}")
            raise HTTPException(
                status_code=404,
                detail="Registration key has invalid company association"
            )
        
        # Enhance key with company information
        enhanced_key = {
            **key,
            "company_name": company.get("name"),
            "organization_code": company.get("organization_code"),
        }
        
        return convert_objectid_to_str(enhanced_key)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get registration key: {str(e)}"
        )
@router.get("/organization/{org_code}", response_model=Dict)
async def get_devices_by_organization(org_code: str):
    """Get all devices for an organization with enhanced status info"""
    try:
        # Get companies to find the one with matching org code
        companies = await repo.list_companies()
        company = next((c for c in companies if c.get("organization_code") == org_code), None)
        
        if not company:
            return {
                "organization_code": org_code,
                "devices": [],
                "total": 0,
                "online": 0,
                "offline": 0
            }
        
        # Get all devices for this company
        devices = await repo.list_digital_screens(company.get("id"))
        
        # Enhance device info with latest heartbeat and credentials status
        enhanced_devices = []
        online_count = 0
        
        for device in devices:
            device_id = device.get("id")
            if not device_id:
                continue  # Skip devices without IDs
            
            # Get latest heartbeat
            latest_heartbeat = await repo.get_latest_heartbeat(device_id)
            
            # Check if device is online (heartbeat within last 5 minutes)
            is_online = False
            if latest_heartbeat:
                heartbeat_time = latest_heartbeat.get("timestamp")
                if isinstance(heartbeat_time, str):
                    heartbeat_time = datetime.fromisoformat(heartbeat_time)
                if heartbeat_time and (datetime.utcnow() - heartbeat_time).seconds < 300:  # 5 minutes
                    is_online = True
                    online_count += 1
            
            # Get credentials status
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get organization devices: {str(e)}"
        )


@router.get("/registration/stats", response_model=Dict)
async def get_registration_statistics():
    """Get device registration statistics and security metrics"""
    try:
        stats = await enhanced_device_registration.get_registration_stats()
        
        # Add additional database stats
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
async def get_device_security_status():
    """Get device security status and monitoring information"""
    try:
        # Get registration stats
        registration_stats = await enhanced_device_registration.get_registration_stats()
        
        # Get device status breakdown
        all_devices = await repo.list_digital_screens()
        device_status_counts = {}
        for device in all_devices:
            status = device.get("status", "unknown")
            device_status_counts[status] = device_status_counts.get(status, 0) + 1
        
        # Check for suspicious activity
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
async def unblock_ip_address(request_data: Dict):
    """Unblock an IP address that was blocked for suspicious activity"""
    try:
        ip_address = request_data.get("ip_address")
        if not ip_address:
            raise HTTPException(status_code=400, detail="IP address is required")
        
        # Remove from blocked IPs
        enhanced_device_registration.blocked_ips.discard(ip_address)
        
        # Reset failed attempts count
        enhanced_device_registration.failed_attempts[ip_address] = 0
        
        logger.info(f"Manually unblocked IP address: {ip_address}")
        
        return {
            "success": True,
            "message": f"IP address {ip_address} has been unblocked",
            "ip_address": ip_address
        }
        
    except Exception as e:
        logger.error(f"Error unblocking IP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to unblock IP: {str(e)}")


# === DEVICE CONTENT MANAGEMENT ===

@router.get("/content/pull/{device_id}")
async def pull_device_content(
    device_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Pull content for a specific device based on its company and permissions.
    This endpoint is used by devices to get their assigned content.
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Device authentication required"
            )
        
        # Authenticate device
        device_token = credentials.credentials
        device = await device_auth_service.authenticate_device(device_id, device_token)
        
        if not device:
            raise HTTPException(
                status_code=401,
                detail="Invalid device credentials"
            )
        
        # Get device's company
        device_company_id = device.get("company_id")
        if not device_company_id:
            raise HTTPException(
                status_code=400,
                detail="Device not associated with a company"
            )
        
        # Get company information
        companies = await repo.list_companies()
        device_company = next((c for c in companies if c.get("id") == device_company_id), None)
        
        if not device_company:
            raise HTTPException(
                status_code=404,
                detail="Device company not found"
            )
        
        # Determine content access based on company type
        accessible_content = []
        
        if device_company.get("company_type") == "HOST":
            # HOST devices can display:
            # 1. Their own content
            # 2. Shared content from ADVERTISER companies they allow
            
            # Get own content
            own_content = await repo.get_content_by_company(device_company_id, status="approved")
            accessible_content.extend(own_content)
            
            # Get shared content (if sharing is enabled)
            if device_company.get("sharing_settings", {}).get("allow_content_sharing", True):
                shared_content = await repo.get_shared_content_for_company(device_company_id)
                accessible_content.extend(shared_content)
        
        elif device_company.get("company_type") == "ADVERTISER":
            # ADVERTISER devices typically only display their own content
            own_content = await repo.get_content_by_company(device_company_id, status="approved")
            accessible_content = own_content
        
        # Update device last seen timestamp
        await repo.update_device_last_seen(device_id, datetime.utcnow())
        
        # Return content list with metadata
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
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve device content"
        )


@router.post("/heartbeat/{device_id}")
async def device_heartbeat(
    device_id: str,
    heartbeat_data: DeviceHeartbeat,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Device health check and status reporting endpoint.
    Devices use this to report their status and receive updates.
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Device authentication required"
            )
        
        # Authenticate device
        device_token = credentials.credentials
        device = await device_auth_service.authenticate_device(device_id, device_token)
        
        if not device:
            raise HTTPException(
                status_code=401,
                detail="Invalid device credentials"
            )
        
        # Update device status
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
        
        # Check for any pending commands/notifications for this device
        pending_commands = await repo.get_device_pending_commands(device_id)
        
        return {
            "success": True,
            "device_id": device_id,
            "status": "acknowledged",
            "server_time": datetime.utcnow().isoformat(),
            "pending_commands": pending_commands,
            "next_heartbeat_seconds": 300  # 5 minutes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Device heartbeat failed for {device_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Heartbeat processing failed"
        )


@router.post("/analytics/{device_id}")
async def report_device_analytics(
    device_id: str,
    analytics_data: Dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Device analytics reporting endpoint.
    Devices report content performance and user interaction data.
    """
    try:
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Device authentication required"
            )
        
        # Authenticate device
        device_token = credentials.credentials
        device = await device_auth_service.authenticate_device(device_id, device_token)
        
        if not device:
            raise HTTPException(
                status_code=401,
                detail="Invalid device credentials"
            )
        
        # Store analytics data
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
        raise HTTPException(
            status_code=500,
            detail="Analytics reporting failed"
        )


@router.delete("/keys/cleanup", response_model=Dict)
async def cleanup_orphaned_keys():
    """Clean up registration keys with invalid company associations"""
    try:
        # Get all registration keys and companies
        keys = await repo.list_device_registration_keys()
        companies = await repo.list_companies()
        
        company_ids = {c.get("id") for c in companies}
        
        # Find orphaned keys
        orphaned_keys = []
        for key in keys:
            company_id = key.get("company_id")
            if company_id not in company_ids:
                orphaned_keys.append(key)
        
        # Delete orphaned keys
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup orphaned keys: {str(e)}"
        )
