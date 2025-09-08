# Clean FastAPI Application
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
from app.config import settings

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
    logger.info("🚀 Starting Adara Screen Digital Signage Platform")
    try:
        await db_service.initialize()
        logger.info("✅ Database service initialized")
        
        # Seed test data for in-memory storage in development
        if not settings.MONGO_URI and settings.ENVIRONMENT == "development":
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
    description="Enterprise Multi-Tenant Digital Signage Platform with Enhanced RBAC",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS based on environment
if settings.ENVIRONMENT == "development":
    # In development, allow all localhost/127.0.0.1 origins to handle dynamic Flutter ports
    cors_origins = [
        "http://localhost:*",  # This won't work, so we'll use a custom function
        "http://127.0.0.1:*",  # This won't work, so we'll use a custom function
    ]
    # For development, we'll allow all origins (less secure but needed for Flutter)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )
else:
    # Production: strict CORS policy
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://*.adara.com", 
            "https://*.vercel.app"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if settings.ENVIRONMENT == "production":
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.include_router(api_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    try:
        if not db_service.connected:
            return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "disconnected"})
        return {"status": "healthy", "database": "connected", "auth_service": "operational", "rbac_system": "active", "version": "2.0.0"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})

@app.get("/")
async def root():
    return {
        "message": "Adara Screen Digital Signage Platform API",
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/api/health",
        "auth_endpoints": {
            "login": "/api/auth/login",
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
        "description": "Enterprise Multi-Tenant Digital Signage Platform with Enhanced RBAC",
        "features": ["Clean RBAC System", "Multi-Company Support", "Device Authentication", "Permission-based Access Control"],
        "authentication": "JWT Bearer Token",
        "database": "MongoDB",
        "documentation": "/api/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.ENVIRONMENT == "development", log_level="info")
