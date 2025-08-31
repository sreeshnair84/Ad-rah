#!/usr/bin/env python3
"""
Simple server startup script
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Import and run the FastAPI app
from app.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
