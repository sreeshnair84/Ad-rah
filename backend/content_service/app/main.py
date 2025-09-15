# Clean FastAPI Application with Enhanced Security
import os
import logging
from contextlib import asynccontextmanager

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Environment variables loaded from .env file")
except ImportError:
    print("[WARNING] python-dotenv not installed, using system environment variables only")

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database_service import db_service
from app.auth_service import auth_service
from app.config import enhanced_config, initialize_config, settings

# Import enhanced security services
from app.security.enhanced_auth_service import initialize_auth_service
from app.security.security_middleware import configure_security_middleware, get_cors_config
from app.security.encryption_service import encryption_service

# Import API router with all endpoints
from app.api import api_router

async def seed_development_data():
    """Seed test data for development with in-memory storage"""
    from app.models import Company, DeviceRegistrationKey
    from app.repo import repo
    from datetime import datetime, timedelta
    import uuid
    
    # Create Dubai Mall company (what Flutter expects)
    company = Company(
        id=str(uuid.uuid4()),
        name='Dubai Mall Digital Displays',
        type='HOST',
        address='Dubai Mall, Downtown Dubai',
        city='Dubai',
        country='UAE',
        organization_code='ORG-DUBAI001',  # Flutter expects this
        status='active'
    )
    
    saved_company = await repo.save_company(company)
    
    # Create the registration key that Flutter is using
    key = DeviceRegistrationKey(
        id=str(uuid.uuid4()),
        key='nZ2CB2bX472WhaOq',  # Flutter expects this
        company_id=saved_company['id'],
        created_by='system',
        expires_at=datetime.utcnow() + timedelta(days=30),  # Valid for 30 days
        used=False,
        used_by_device=None
    )
    
    await repo.save_device_registration_key(key)
    
    logger.info("✅ Created Dubai Mall company and registration key for development")
    logger.info(f"✅ Organization Code: ORG-DUBAI001")
    logger.info(f"✅ Registration Key: nZ2CB2bX472WhaOq")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Adara Screen Digital Signage Platform with Enhanced Security")
    try:
        # Initialize configuration with secrets
        await initialize_config()
        logger.info("✅ Configuration and secrets initialized")
        
        # Initialize encryption service
        if enhanced_config.ENCRYPTION_KEY:
            # For now, use a single key. In production, this would come from Key Vault
            encryption_keys = {"default": enhanced_config.ENCRYPTION_KEY}
            await encryption_service.initialize(encryption_keys)
            logger.info("✅ Encryption service initialized")
        
        # Initialize enhanced authentication service
        if enhanced_config.JWT_SECRET_KEY and enhanced_config.JWT_REFRESH_SECRET_KEY:
            await initialize_auth_service(
                jwt_secret=enhanced_config.JWT_SECRET_KEY,
                refresh_secret=enhanced_config.JWT_REFRESH_SECRET_KEY,
                redis_url=enhanced_config.REDIS_URL
            )
            logger.info("✅ Enhanced authentication service initialized")
        else:
            logger.warning("JWT secrets not available, authentication service not initialized")
        
        # Initialize database
        await db_service.initialize()
        logger.info("✅ Database service initialized")
        
        # Seed test data for in-memory storage in development
        if not enhanced_config.MONGO_URI and enhanced_config.ENVIRONMENT == "development":
            await seed_development_data()
            logger.info("✅ Development test data seeded")
        
        yield
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        await db_service.close()
        logger.info("🔌 Database connections closed")

app = FastAPI(
    title="Adara Screen Digital Signage Platform",
    description="Enterprise Multi-Tenant Digital Signage Platform with Enhanced Security and RBAC",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure security middleware
configure_security_middleware(
    app,
    environment=enhanced_config.ENVIRONMENT,
    allowed_hosts=enhanced_config.ALLOWED_HOSTS,
    enable_rate_limiting=enhanced_config.ENABLE_RATE_LIMITING,
    requests_per_minute=enhanced_config.RATE_LIMIT_REQUESTS_PER_MINUTE
)

# Configure CORS with security-aware settings
cors_config = get_cors_config(enhanced_config.ENVIRONMENT)
app.add_middleware(CORSMiddleware, **cors_config)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if enhanced_config.ENVIRONMENT == "production":
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.include_router(api_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    try:
        if not db_service.connected:
            return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "disconnected"})
        
        # Check security services status
        security_status = {
            "key_vault": enhanced_config.key_vault_service is not None,
            "encryption": encryption_service._initialized,
            "authentication": "operational"
        }
        
        return {
            "status": "healthy", 
            "database": "connected", 
            "auth_service": "operational", 
            "rbac_system": "active", 
            "security": security_status,
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})

@app.get("/")
async def root():
    return {
        "message": "Adara Screen Digital Signage Platform API",
        "version": "2.0.0",
        "security_features": [
            "Enhanced JWT Authentication",
            "Refresh Token Support", 
            "Azure Key Vault Integration",
            "Field-level PII Encryption",
            "Security Headers",
            "Rate Limiting",
            "RBAC System"
        ],
        "docs": "/api/docs",
        "health": "/api/health",
        "auth_endpoints": {
            "login": "/api/auth/login",
            "refresh": "/api/auth/refresh",
            "logout": "/api/auth/logout",
            "user_profile": "/api/auth/me",
            "users": "/api/auth/users",
            "companies": "/api/auth/companies"
        }
    }

@app.get("/api")
async def api_info():
    return {
        "title": "Adara Screen Digital Signage Platform API",
        "version": "2.0.0",
        "description": "Enterprise Multi-Tenant Digital Signage Platform with Enhanced Security and RBAC",
        "features": [
            "Enhanced Security Architecture",
            "Clean RBAC System", 
            "Multi-Company Support", 
            "Device Authentication", 
            "Permission-based Access Control",
            "Azure Key Vault Integration",
            "Field-level Encryption",
            "Refresh Token Authentication"
        ],
        "authentication": "JWT Bearer Token with Refresh",
        "database": "MongoDB",
        "documentation": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=enhanced_config.ENVIRONMENT == "development", log_level="info")
