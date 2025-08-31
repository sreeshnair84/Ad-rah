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
        # Verify the company exists
        companies = await repo.list_companies()
        company = next((c for c in companies if c.get("id") == key_request.company_id), None)
        
        if not company:
            logger.warning(f"Company not found: {key_request.company_id}")
            raise HTTPException(
                status_code=400,
                detail="Company not found"
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
            "company_name": company.get("name"),
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


@router.post("/register", response_model=Dict)
async def register_device(
    device_data: DeviceRegistrationCreate,
    request: Request
):
    """Register a new device with enhanced security and authentication"""
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
            "message": "Device registered successfully with authentication",
            "organization_code": device_data.organization_code,
            "company_name": matching_company.get("name"),
            "ip_address": client_ip,
            "mac_address": client_mac,
            # Authentication credentials
            "certificate": auth_result.get("certificate"),
            "private_key": auth_result.get("private_key"),  # Only provided once
            "jwt_token": auth_result.get("jwt_token"),
            "refresh_token": auth_result.get("refresh_token"),
            "token_expires_in": auth_result.get("expires_in")
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
        # Get all registration keys
        keys = await repo.list_device_registration_keys()
        
        # Get all companies for lookup
        companies = await repo.list_companies()
        company_lookup = {c.get("id"): c for c in companies}
        
        # Enhance keys with company information
        enhanced_keys = []
        for key in keys:
            company = company_lookup.get(key.get("company_id"))
            enhanced_key = {
                **key,
                "company_name": company.get("name") if company else "Unknown Company",
                "organization_code": company.get("organization_code") if company else None,
            }
            enhanced_keys.append(convert_objectid_to_str(enhanced_key))
        
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
        
        # Enhance key with company information
        enhanced_key = {
            **key,
            "company_name": company.get("name") if company else "Unknown Company",
            "organization_code": company.get("organization_code") if company else None,
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
