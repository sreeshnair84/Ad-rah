#!/usr/bin/env python3
"""Debug navigation API endpoint for testing"""

import asyncio
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Set environment variable BEFORE importing anything
os.environ['MONGO_URI'] = 'mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin'

from app.database_service import db_service

app = FastAPI()

@app.get("/debug/navigation/{email}")
async def debug_navigation(email: str):
    """Debug endpoint to check navigation for a user"""
    try:
        await db_service.initialize()
        
        # Get user by email
        user_data = await db_service.get_user_by_email(email)
        if not user_data:
            return JSONResponse({"error": "User not found"}, status_code=404)
        
        user_id = user_data['id']
        
        # Get user profile with navigation
        user_profile = await db_service.get_user_profile(user_id)
        if not user_profile:
            return JSONResponse({"error": "Profile not found"}, status_code=404)
        
        return {
            "email": email,
            "user_id": user_id,
            "user_type": user_profile.user_type,
            "navigation_count": len(user_profile.accessible_navigation),
            "navigation": user_profile.accessible_navigation
        }
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)