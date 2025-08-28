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
    print("Starting application lifespan...")
    await worker.start()
    await event_processor.start()
    print("Workers started, initializing default data...")
    await init_default_data()
    print("Default data initialization completed")
    yield
    await worker.stop()
    await event_processor.stop()

app = FastAPI(title="Adārah from Hebron - Content Service", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Add this for Next.js dev server (alternative port)
        "http://127.0.0.1:3001",  # Add this for Next.js dev server (alternative port)
        "http://localhost:8000",  # Add this for Next.js proxy
        "http://127.0.0.1:8000"   # Add this for Next.js proxy
    ],  # Frontend URLs and Next.js proxy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
