#!/usr/bin/env python3
"""
Server startup script with MongoDB
"""
import sys
import os

# Set MongoDB environment variable
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/openkiosk'

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import and run the FastAPI app
from app.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
