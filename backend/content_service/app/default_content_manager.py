"""
Default Content Management System
Provides centralized management of fallback content for devices
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from app.models import ContentMeta

logger = logging.getLogger(__name__)

class DefaultContentManager:
    """Centralized manager for default content shown when no specific content is assigned"""
    
    def __init__(self):
        self.default_content_items = [
            {
                "id": "default-welcome",
                "title": "Welcome to Adara Digital Signage",
                "description": "Welcome message for all devices",
                "content_type": "text/html",
                "content_data": {
                    "html": """
                    <div style="text-align: center; padding: 40px; font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; height: 100vh; display: flex; flex-direction: column; justify-content: center;">
                        <h1 style="font-size: 4em; margin-bottom: 0.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">Welcome to Adara™</h1>
                        <h2 style="font-size: 2em; margin-bottom: 1em; font-weight: normal; opacity: 0.9;">Digital Signage Platform</h2>
                        <p style="font-size: 1.5em; opacity: 0.8; max-width: 800px; margin: 0 auto; line-height: 1.6;">Experience the future of digital communication</p>
                    </div>
                    """,
                    "duration": 8000
                },
                "categories": ["default", "welcome"],
                "tags": ["system", "default", "welcome"],
                "priority": 10,
                "is_system": True
            },
            {
                "id": "default-logo",
                "title": "Adara from Hebron™ Logo",
                "description": "Company branding logo display",
                "content_type": "text/html",
                "content_data": {
                    "html": """
                    <div style="display: flex; align-items: center; justify-content: center; height: 100vh; background: #ffffff;">
                        <div style="text-align: center;">
                            <div style="font-size: 6em; color: #1E3A8A; margin-bottom: 0.2em; font-weight: bold; font-family: 'Georgia', serif;">
                                Adara™
                            </div>
                            <div style="font-size: 2em; color: #3B82F6; margin-bottom: 0.5em; font-style: italic;">
                                from Hebron
                            </div>
                            <div style="width: 200px; height: 3px; background: linear-gradient(90deg, #1E3A8A, #3B82F6); margin: 20px auto;"></div>
                            <div style="font-size: 1.5em; color: #6B7280; font-weight: normal;">
                                Digital Signage Solutions
                            </div>
                        </div>
                    </div>
                    """,
                    "duration": 6000
                },
                "categories": ["default", "branding"],
                "tags": ["system", "logo", "branding"],
                "priority": 9,
                "is_system": True
            },
            {
                "id": "default-features",
                "title": "Platform Features",
                "description": "Showcase of platform capabilities",
                "content_type": "text/html",
                "content_data": {
                    "html": """
                    <div style="padding: 40px; font-family: Arial, sans-serif; background: linear-gradient(45deg, #f0f9ff 0%, #e0e7ff 100%); height: 100vh; box-sizing: border-box;">
                        <div style="max-width: 1200px; margin: 0 auto; height: 100%;">
                            <h1 style="text-align: center; font-size: 3em; color: #1E3A8A; margin-bottom: 1em;">Platform Features</h1>
                            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 40px; height: 70%;">
                                <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); text-align: center;">
                                    <div style="font-size: 3em; color: #3B82F6; margin-bottom: 20px;">📱</div>
                                    <h3 style="color: #1E3A8A; font-size: 1.8em; margin-bottom: 15px;">Remote Management</h3>
                                    <p style="color: #6B7280; font-size: 1.2em; line-height: 1.6;">Manage all your displays from anywhere with our web-based dashboard</p>
                                </div>
                                <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); text-align: center;">
                                    <div style="font-size: 3em; color: #3B82F6; margin-bottom: 20px;">🎯</div>
                                    <h3 style="color: #1E3A8A; font-size: 1.8em; margin-bottom: 15px;">Smart Content</h3>
                                    <p style="color: #6B7280; font-size: 1.2em; line-height: 1.6;">AI-powered content moderation and intelligent scheduling</p>
                                </div>
                                <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); text-align: center;">
                                    <div style="font-size: 3em; color: #3B82F6; margin-bottom: 20px;">📊</div>
                                    <h3 style="color: #1E3A8A; font-size: 1.8em; margin-bottom: 15px;">Analytics</h3>
                                    <p style="color: #6B7280; font-size: 1.2em; line-height: 1.6;">Real-time performance metrics and audience engagement data</p>
                                </div>
                                <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); text-align: center;">
                                    <div style="font-size: 3em; color: #3B82F6; margin-bottom: 20px;">🔒</div>
                                    <h3 style="color: #1E3A8A; font-size: 1.8em; margin-bottom: 15px;">Enterprise Security</h3>
                                    <p style="color: #6B7280; font-size: 1.2em; line-height: 1.6;">Bank-level security with device authentication and encryption</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    "duration": 12000
                },
                "categories": ["default", "information"],
                "tags": ["system", "features", "information"],
                "priority": 8,
                "is_system": True
            },
            {
                "id": "default-status",
                "title": "System Status",
                "description": "Device status and connection information",
                "content_type": "text/html",
                "content_data": {
                    "html": """
                    <div style="padding: 40px; font-family: 'Courier New', monospace; background: #0f172a; color: #e2e8f0; height: 100vh; box-sizing: border-box;">
                        <div style="max-width: 800px; margin: 0 auto;">
                            <div style="text-align: center; margin-bottom: 2em;">
                                <h1 style="color: #22c55e; font-size: 2.5em; margin-bottom: 0.5em;">● SYSTEM ONLINE</h1>
                                <p style="color: #94a3b8; font-size: 1.2em;">Adara Digital Signage Platform</p>
                            </div>
                            
                            <div style="background: #1e293b; padding: 30px; border-radius: 10px; border-left: 4px solid #22c55e;">
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                                    <div>
                                        <div style="color: #64748b; font-size: 0.9em; margin-bottom: 5px;">STATUS</div>
                                        <div style="color: #22c55e; font-size: 1.3em; font-weight: bold;">● CONNECTED</div>
                                    </div>
                                    <div>
                                        <div style="color: #64748b; font-size: 0.9em; margin-bottom: 5px;">UPTIME</div>
                                        <div style="color: #e2e8f0; font-size: 1.3em;">Running</div>
                                    </div>
                                    <div>
                                        <div style="color: #64748b; font-size: 0.9em; margin-bottom: 5px;">MODE</div>
                                        <div style="color: #3b82f6; font-size: 1.3em;">Demo</div>
                                    </div>
                                    <div>
                                        <div style="color: #64748b; font-size: 0.9em; margin-bottom: 5px;">VERSION</div>
                                        <div style="color: #e2e8f0; font-size: 1.3em;">v1.0.0</div>
                                    </div>
                                </div>
                                
                                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #334155;">
                                    <div style="color: #94a3b8; font-size: 1em; text-align: center;">
                                        Waiting for content assignment...
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    "duration": 10000
                },
                "categories": ["default", "status"],
                "tags": ["system", "status", "monitoring"],
                "priority": 7,
                "is_system": True
            }
        ]
    
    async def get_default_content(self, device_id: Optional[str] = None, 
                                company_id: Optional[str] = None) -> List[Dict]:
        """
        Get default content for a device
        
        Args:
            device_id: ID of the device requesting content
            company_id: Company ID for company-specific defaults
            
        Returns:
            List of default content items
        """
        try:
            logger.info(f"Generating default content for device {device_id}, company {company_id}")
            
            # Convert internal format to ContentMeta-like structure
            content_items = []
            current_time = datetime.utcnow()
            
            for item in self.default_content_items:
                content_item = {
                    "id": item["id"],
                    "title": item["title"],
                    "description": item["description"],
                    "content_type": item["content_type"],
                    "content_data": item["content_data"],
                    "categories": item["categories"],
                    "tags": item["tags"],
                    "status": "approved",  # Default content is always approved
                    "owner_id": "system",
                    "created_at": current_time.isoformat(),
                    "updated_at": current_time.isoformat(),
                    "priority": item["priority"],
                    "is_system": item.get("is_system", True),
                    "filename": f"{item['id']}.html",
                    "size": len(str(item["content_data"]))
                }
                
                # Add device-specific or company-specific customization
                if device_id:
                    content_item["content_data"]["device_id"] = device_id
                if company_id:
                    content_item["content_data"]["company_id"] = company_id
                
                content_items.append(content_item)
            
            # Sort by priority (higher first)
            content_items.sort(key=lambda x: x["priority"], reverse=True)
            
            logger.info(f"Returning {len(content_items)} default content items")
            return content_items
            
        except Exception as e:
            logger.error(f"Error generating default content: {e}")
            # Return minimal fallback
            return [{
                "id": "minimal-fallback",
                "title": "Adara Digital Signage",
                "description": "System default content",
                "content_type": "text/html",
                "content_data": {
                    "html": "<div style='text-align: center; padding: 100px; font-family: Arial; font-size: 3em; color: #1E3A8A;'>Adara™<br><small style='font-size: 0.5em; color: #6B7280;'>Digital Signage Platform</small></div>",
                    "duration": 5000
                },
                "categories": ["default"],
                "tags": ["system", "fallback"],
                "status": "approved",
                "owner_id": "system",
                "priority": 1,
                "is_system": True
            }]
    
    async def get_demo_content(self, device_id: str) -> List[Dict]:
        """
        Get demo content for unregistered devices
        
        Args:
            device_id: ID of the demo device
            
        Returns:
            List of demo content items with device-specific messaging
        """
        try:
            # Get base default content
            demo_content = await self.get_default_content(device_id=device_id)
            
            # Add demo-specific welcome message at the beginning
            demo_welcome = {
                "id": f"demo-welcome-{device_id}",
                "title": "Demo Mode - Device Not Registered",
                "description": f"Demo welcome for device {device_id}",
                "content_type": "text/html",
                "content_data": {
                    "html": f"""
                    <div style="background: linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%); color: white; height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; font-family: Arial, sans-serif; text-align: center; padding: 40px; box-sizing: border-box;">
                        <div style="background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; backdrop-filter: blur(10px); max-width: 800px;">
                            <h1 style="font-size: 3.5em; margin-bottom: 0.3em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🚀 Demo Mode</h1>
                            <h2 style="font-size: 1.8em; margin-bottom: 1em; opacity: 0.9; font-weight: normal;">Device Not Registered</h2>
                            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin: 20px 0;">
                                <p style="font-size: 1.2em; margin: 0; font-family: 'Courier New', monospace;">Device ID: {device_id[:16]}...</p>
                            </div>
                            <p style="font-size: 1.3em; line-height: 1.6; opacity: 0.9; margin-bottom: 1.5em;">
                                This device is showing demo content. To register this device and access full features:
                            </p>
                            <div style="text-align: left; max-width: 600px; margin: 0 auto;">
                                <p style="font-size: 1.1em; margin: 15px 0;">📱 1. Access the admin dashboard</p>
                                <p style="font-size: 1.1em; margin: 15px 0;">🔑 2. Generate a registration key</p>
                                <p style="font-size: 1.1em; margin: 15px 0;">📋 3. Register this device</p>
                                <p style="font-size: 1.1em; margin: 15px 0;">🎯 4. Assign custom content</p>
                            </div>
                        </div>
                    </div>
                    """,
                    "duration": 15000
                },
                "categories": ["demo", "registration"],
                "tags": ["demo", "registration", "unregistered"],
                "status": "approved",
                "owner_id": "system",
                "priority": 15,  # Highest priority for demo content
                "is_system": True,
                "is_demo": True
            }
            
            # Insert demo welcome at the beginning
            demo_content.insert(0, demo_welcome)
            
            logger.info(f"Generated demo content with {len(demo_content)} items for device {device_id}")
            return demo_content
            
        except Exception as e:
            logger.error(f"Error generating demo content: {e}")
            return await self.get_default_content(device_id=device_id)
    
    async def should_show_default_content(self, device_id: str, 
                                        assigned_content: List[Dict]) -> bool:
        """
        Determine if default content should be shown
        
        Args:
            device_id: ID of the device
            assigned_content: Content specifically assigned to the device
            
        Returns:
            True if default content should be shown
        """
        # Show default content if no assigned content or all assigned content is unavailable
        if not assigned_content:
            logger.info(f"No assigned content for device {device_id}, showing default content")
            return True
        
        # Check if assigned content is valid and approved
        valid_content = [
            content for content in assigned_content
            if content.get("status") == "approved" and content.get("content_data")
        ]
        
        if not valid_content:
            logger.info(f"No valid assigned content for device {device_id}, showing default content")
            return True
        
        return False

# Global instance
default_content_manager = DefaultContentManager()