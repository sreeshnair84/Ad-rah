# Load environment variables FIRST - before any other imports
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Environment variables loaded from .env file")
except ImportError:
    print("[WARNING] python-dotenv not installed, using system environment variables only")

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import fallback components
from app.api import api_router
from app.auth import init_default_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    logger.info("🚀 Starting Adārah Digital Signage Platform")
    
    # Initialize database service layer
    try:
        from app.database import initialize_database_from_url, DatabaseProvider
        from app.config import settings
        
        # Check environment variables
        mongo_uri = getattr(settings, "MONGO_URI", None)
        secret_key = getattr(settings, "SECRET_KEY", None)
        logger.info(f"MONGO_URI configured: {mongo_uri is not None}")
        logger.info(f"SECRET_KEY configured: {secret_key is not None}")
        
        # Initialize database service
        if mongo_uri:
            logger.info("🔌 Initializing database connection...")
            db_initialized = await initialize_database_from_url(mongo_uri)
            
            if db_initialized:
                logger.info("✅ DATABASE SERVICE INITIALIZED - Using MongoDB")
                
                # Initialize RBAC and default data
                try:
                    await init_default_data()
                    logger.info("✅ Default data and RBAC system initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to initialize default data: {e}")
            else:
                logger.error("❌ Failed to initialize database service")
                raise RuntimeError("Database initialization failed")
        else:
            # Fallback to old repo system for development
            logger.warning("⚠️ No MONGO_URI found - using legacy in-memory storage")
            from app.repo import repo, persistence_enabled
            
            if not persistence_enabled:
                logger.warning("💾 TEMPORARY STORAGE - Data will be LOST on restart!")
            
            # Initialize with old system
            await init_default_data()
            logger.info("✅ Legacy storage initialized")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        # Don't raise the exception, let the app start anyway for debugging
        
    logger.info("✅ Application startup complete!")
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Shutting down application...")
    try:
        from app.database import close_database
        await close_database()
        logger.info("🔌 Database connections closed")
    except Exception as e:
        logger.warning(f"⚠️ Error during shutdown: {e}")

# Create FastAPI app
app = FastAPI(
    title="Adārah Digital Signage API",
    description="Content management system for digital signage with multi-tenant architecture and RBAC",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS - SECURITY: Restrict for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3001",
        "http://localhost:8080",  # Flutter web dev server
        "http://127.0.0.1:8080",
        "http://localhost:5000",  # Flutter web alternative
        "http://127.0.0.1:5000",
        "*",  # Allow all origins for development (restrict for production!)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Adārah Digital Signage API is running"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Adārah Digital Signage API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/admin/init-data")
async def initialize_data():
    """Initialize authentication data (admin endpoint)"""
    try:
        from app.repo import repo
        
        # Clear and initialize
        if hasattr(repo, '_store'):
            repo._store.clear()
        
        await init_default_data()
        
        # Show result
        if hasattr(repo, '_store'):
            users = repo._store.get("__users__", {})
            return {
                "success": True,
                "message": "Data initialized successfully",
                "users_created": len(users),
                "user_emails": [user.get("email") for user in users.values()]
            }
        else:
            return {"success": True, "message": "MongoDB data initialized"}
            
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "details": traceback.format_exc()
        }

# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    logger.info(f"Starting server on {host}:{port} (reload={reload})")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload
    )
