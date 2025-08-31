from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api import api_router
from app.auth import init_default_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[STARTUP] Initializing Adarah Kiosk Service...")
    
    # Initialize authentication data - THIS IS CRITICAL
    try:
        from app.repo import repo
        print("[STARTUP] Checking authentication data...")
        
        if hasattr(repo, '_store'):
            existing_users = len(repo._store.get("__users__", {}))
            print(f"[STARTUP] Found {existing_users} existing users")
            
            if existing_users == 0:
                print("[STARTUP] No users found, initializing default data...")
                await init_default_data()
                new_users = len(repo._store.get("__users__", {}))
                print(f"[STARTUP] SUCCESS: {new_users} users initialized")
                
                # Show created users for verification
                users = repo._store.get("__users__", {})
                for uid, user in users.items():
                    print(f"[STARTUP]   User: {user.get('email')}")
            else:
                print(f"[STARTUP] Using existing {existing_users} users")
        else:
            print("[STARTUP] Using MongoDB - initializing data...")
            await init_default_data()
            print("[STARTUP] MongoDB data initialized")
            
    except Exception as e:
        print(f"[STARTUP] CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Continue anyway to allow debugging
    
    print("[STARTUP] Adarah Kiosk Service ready for requests!")
    yield
    print("[SHUTDOWN] Service stopping...")

app = FastAPI(title="Adarah from Hebron - Content Service", lifespan=lifespan)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,  # Allow credentials (Authorization headers)
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
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