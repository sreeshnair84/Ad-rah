from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import api_router
from app.moderation_worker import worker
from app.event_processor import event_processor
from app.auth import init_default_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Adarah Kiosk Service...")
    
    # Initialize core services
    try:
        print("Initializing background services...")
        await worker.start()
        await event_processor.start()
        print("Background services started successfully")
    except Exception as e:
        print(f"Warning: Background services failed: {e}")
        # Continue without background services for development
    
    # Initialize authentication data
    try:
        print("Initializing authentication data...")
        from app.repo import repo
        
        # Check if data already exists
        if hasattr(repo, '_store'):
            existing_users = len(repo._store.get("__users__", {}))
            if existing_users == 0:
                print("No existing users found, initializing default data...")
                await init_default_data()
                new_users = len(repo._store.get("__users__", {}))
                print(f"Authentication initialized: {new_users} users created")
            else:
                print(f"Authentication data exists: {existing_users} users found")
        else:
            print("Using MongoDB for authentication data")
            await init_default_data()
            print("MongoDB authentication data initialized")
            
    except Exception as e:
        print(f"CRITICAL: Authentication initialization failed: {e}")
        import traceback
        traceback.print_exc()
        # This is critical, so we should still start the server but log the error
    
    print("Adarah Kiosk Service is ready!")
    
    yield
    
    # Cleanup
    print("Shutting down services...")
    try:
        await worker.stop()
        await event_processor.stop()
        print("Services shut down cleanly")
    except Exception as e:
        print(f"Warning during shutdown: {e}")

# Temporarily disable lifespan for debugging
app = FastAPI(title="Adārah from Hebron - Content Service")

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js frontend (primary)
        "http://127.0.0.1:3000",  # Next.js frontend (alternative)
        "http://localhost:3001",  # Next.js dev server (alternative port)
        "http://127.0.0.1:3001",  # Next.js dev server (alternative port)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/admin/init-data")
async def initialize_data():
    """Initialize authentication data (no auth required)"""
    try:
        from app.auth import init_default_data
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
