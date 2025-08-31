#!/usr/bin/env python3
"""
Startup script that ensures MongoDB persistent storage is properly configured
and starts the OpenKiosk backend service.
"""
import os
import sys
import subprocess
import time
import logging
import asyncio
from pathlib import Path

# Add the current directory to Python path so we can import from app
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.repo import repo, MongoRepo, InMemoryRepo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_mongodb_connection():
    """Check if MongoDB is running and accessible"""
    try:
        import pymongo
        client = pymongo.MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        client.server_info()
        logger.info("✅ MongoDB connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        return False

def start_mongodb_service():
    """Attempt to start MongoDB service if not running"""
    try:
        # Try to start MongoDB service on Windows
        if os.name == 'nt':
            subprocess.run(['net', 'start', 'MongoDB'], check=False, capture_output=True)
        # Try to start on Unix-like systems
        else:
            subprocess.run(['sudo', 'systemctl', 'start', 'mongod'], check=False, capture_output=True)
        
        time.sleep(3)  # Give MongoDB time to start
        return check_mongodb_connection()
    except Exception as e:
        logger.warning(f"Could not start MongoDB service: {e}")
        return False

def ensure_mongodb_ready():
    """Ensure MongoDB is running and ready for connections"""
    logger.info("🔍 Checking MongoDB availability...")
    
    # First check if MongoDB is already running
    if check_mongodb_connection():
        return True
    
    # Try to start MongoDB service
    logger.info("🚀 Attempting to start MongoDB service...")
    if start_mongodb_service():
        return True
    
    # If we can't start MongoDB, warn the user
    logger.warning("""
⚠️  WARNING: Could not connect to MongoDB!
    
This means your data will NOT persist between restarts.
    
To fix this:
1. Install MongoDB: https://www.mongodb.com/try/download/community
2. Start MongoDB service:
   - Windows: net start MongoDB
   - Linux/Mac: sudo systemctl start mongod
3. Or set MONGO_URI environment variable to your MongoDB connection string

For now, continuing with in-memory storage (data will be lost on restart)...
""")
    return False

async def initialize_default_data():
    """Initialize default data if using fresh database"""
    try:
        from app.auth import init_default_data
        await init_default_data()
        logger.info("✅ Default data initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize default data: {e}")

def validate_repository():
    """Validate that the repository is properly configured"""
    if isinstance(repo, MongoRepo):
        logger.info("✅ Using MongoDB for persistent storage")
        return True
    elif isinstance(repo, InMemoryRepo):
        logger.warning("⚠️  Using in-memory storage - data will be lost on restart!")
        return False
    else:
        logger.error("❌ Unknown repository type!")
        return False

async def main():
    """Main startup routine"""
    logger.info("🚀 Starting OpenKiosk Backend with Persistent Storage Check...")
    
    # Check MongoDB availability
    mongodb_available = ensure_mongodb_ready()
    
    # Validate repository configuration
    persistent_storage = validate_repository()
    
    # Initialize default data if needed
    if persistent_storage or not mongodb_available:
        await initialize_default_data()
    
    # Print final status
    if persistent_storage:
        logger.info("✅ Backend ready with PERSISTENT storage")
    else:
        logger.warning("⚠️  Backend ready with TEMPORARY storage (data will be lost on restart)")
    
    # Start the FastAPI application
    logger.info("🌐 Starting FastAPI server...")
    
    # Import and run the app
    try:
        import uvicorn
        from app.main import app
        
        # Run with uvicorn
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000, 
            reload=False,  # Disable reload in production
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run async main function
    asyncio.run(main())