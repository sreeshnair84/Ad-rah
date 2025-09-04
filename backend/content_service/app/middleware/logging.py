"""
Request Logging Middleware
=========================

Middleware to log all incoming requests and responses for debugging authentication issues.
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import json

# Create a simple console logger to avoid uvicorn logger conflicts
logger = logging.getLogger("middleware")
logger.setLevel(logging.INFO)

# Only add handler if it doesn't exist
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    logger.propagate = False  # Prevent propagation to avoid conflicts

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Get request info
        method = request.method
        url = str(request.url)
        headers = dict(request.headers)
        
        # Read request body if it's JSON
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Reset the request body for downstream processing
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive
                    
                    # Try to parse as JSON for logging (mask passwords)
                    try:
                        request_body = json.loads(body.decode())
                        # Mask sensitive fields
                        if isinstance(request_body, dict):
                            masked_body = request_body.copy()
                            if 'password' in masked_body:
                                masked_body['password'] = '***'
                            request_body = masked_body
                    except:
                        request_body = f"<binary data: {len(body)} bytes>"
            except Exception as e:
                logger.warning(f"Failed to read request body: {e}")
        
        # Log request
        print(f"🔵 {method} {url}")
        if request_body:
            print(f"   📤 Request body: {request_body}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            status_code = response.status_code
            
            # Try to read response body for logging
            response_body = None
            if hasattr(response, 'body'):
                try:
                    if isinstance(response, StreamingResponse):
                        # Don't try to read streaming responses
                        response_body = "<streaming response>"
                    else:
                        # For regular responses, try to read the body
                        response_body = "<response body>"
                except:
                    response_body = "<unreadable response>"
            
            # Determine log level based on status
            if status_code >= 500:
                log_level = "error"
                emoji = "🔴"
            elif status_code >= 400:
                log_level = "warning" 
                emoji = "🟡"
            else:
                log_level = "info"
                emoji = "🟢"
            
            # Log response with safe logger
            print(f"{emoji} {method} {url} -> {status_code} ({process_time:.3f}s)")
            logger.info(f"{emoji} {method} {url} -> {status_code} ({process_time:.3f}s)")
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            print(f"🔴 {method} {url} -> ERROR ({process_time:.3f}s): {str(e)}")
            logger.error(f"🔴 {method} {url} -> ERROR ({process_time:.3f}s): {str(e)}")
            raise


class AuthLoggingMiddleware(BaseHTTPMiddleware):
    """Specific middleware for authentication-related logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Only log auth-related requests
        if not any(path in str(request.url) for path in ['/auth/', '/login', '/token']):
            return await call_next(request)
        
        print(f"🔐 AUTH REQUEST: {request.method} {request.url}")
        logger.info(f"🔐 AUTH REQUEST: {request.method} {request.url}")
        
        # Log headers (excluding sensitive ones)
        auth_headers = {}
        for key, value in request.headers.items():
            if key.lower() in ['authorization', 'x-api-key']:
                auth_headers[key] = f"{value[:10]}..." if len(value) > 10 else "***"
            elif key.lower() in ['content-type', 'user-agent', 'accept']:
                auth_headers[key] = value
        
        if auth_headers:
            print(f"🔐 AUTH HEADERS: {auth_headers}")
            logger.info(f"🔐 AUTH HEADERS: {auth_headers}")
        
        try:
            response = await call_next(request)
            
            if response.status_code >= 400:
                print(f"🔐 AUTH FAILED: {response.status_code}")
                logger.info(f"🔐 AUTH FAILED: {response.status_code}")
            else:
                print(f"🔐 AUTH SUCCESS: {response.status_code}")
                logger.info(f"🔐 AUTH SUCCESS: {response.status_code}")
            
            return response
            
        except Exception as e:
            print(f"🔐 AUTH ERROR: {str(e)}")
            logger.info(f"🔐 AUTH ERROR: {str(e)}")
            raise
