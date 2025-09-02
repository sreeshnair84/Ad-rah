#!/usr/bin/env python3
"""
Debug JWT token validation
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from app.services.auth_service import AuthService

router = APIRouter(prefix="/debug", tags=["Debug"])
logger = logging.getLogger(__name__)

class TokenRequest(BaseModel):
    token: str

@router.post("/validate-token")
async def debug_validate_token(request: TokenRequest):
    """Test JWT token validation"""
    try:
        auth_service = AuthService()
        token = request.token
        
        result = {
            "token_provided": token[:50] + "..." if len(token) > 50 else token,
            "validation_result": None,
            "error": None
        }
        
        # Test token validation
        try:
            # First decode the token to see its contents
            import jwt
            from datetime import datetime, timezone
            
            try:
                payload = jwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
                current_time = datetime.utcnow().timestamp()
                current_time_tz = datetime.now(timezone.utc).timestamp()
                result["token_payload"] = {
                    "sub": payload.get("sub"),
                    "exp": payload.get("exp"),
                    "iat": payload.get("iat"),
                    "current_timestamp": current_time,
                    "current_timestamp_tz": current_time_tz,
                    "expires_in": payload.get("exp") - current_time if payload.get("exp") else None,
                    "is_expired": current_time > payload.get("exp") if payload.get("exp") else False
                }
            except Exception as decode_error:
                result["token_payload"] = {"decode_error": str(decode_error)}
            
            # Try direct JWT decode with validation to see the exact error
            try:
                jwt.decode(token, auth_service.jwt_secret, algorithms=[auth_service.jwt_algorithm])
                result["direct_jwt_validation"] = {"success": True}
            except jwt.ExpiredSignatureError as e:
                result["direct_jwt_validation"] = {"success": False, "error": "ExpiredSignatureError", "details": str(e)}
            except Exception as e:
                result["direct_jwt_validation"] = {"success": False, "error": type(e).__name__, "details": str(e)}
            
            validation_result = await auth_service.validate_access_token(token)
            result["validation_result"] = {
                "success": validation_result.success,
                "data": validation_result.data if validation_result.success else None,
                "error": validation_result.error if not validation_result.success else None
            }
        except Exception as validation_error:
            result["validation_result"] = {
                "success": False,
                "error": str(validation_error)
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Token validation debug error: {e}")
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")
