"""Compatibility shim for device authentication.

Some modules import authenticate_device from app.security.device_auth; the actual
implementation lives in app.device_auth. Re-export here to avoid import errors.
"""
try:
    from app.device_auth import authenticate_device
except Exception:
    # Fallback stub for environments where device_auth isn't available yet
    async def authenticate_device(*args, **kwargs):
        return {"device_id": "unknown", "authenticated": False}

__all__ = ["authenticate_device"]
