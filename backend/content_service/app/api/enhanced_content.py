#!/usr/bin/env python3

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Optional
import asyncio
from datetime import datetime, timedelta

from ..models.enhanced_content import *
from ..database_service import db_service
from ..auth_service import get_current_user, get_user_company_context

router = APIRouter(prefix="/api/enhanced-content", tags=["Enhanced Content Management"])

# ============================================================================
# CONTENT LAYOUT MANAGEMENT
# ============================================================================

@router.post("/layouts", response_model=Dict)
async def create_content_layout(
    layout: ContentLayoutCreate,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new multi-zone content layout"""
    try:
        # Validate user permissions
        if not company_context["accessible_companies"]:
            raise HTTPException(status_code=403, detail="No accessible companies")
        
        # Create layout document
        layout_doc = {
            **layout.dict(),
            "id": str(uuid.uuid4()),
            "created_by": current_user["id"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save to database
        result = await db_service.db.content_layouts.insert_one(layout_doc)
        layout_doc["_id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "layout_id": layout_doc["id"],
            "message": "Content layout created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create layout: {str(e)}")


@router.get("/layouts", response_model=List[Dict])
async def list_content_layouts(
    company_id: Optional[str] = None,
    layout_type: Optional[str] = None,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """List content layouts with filtering"""
    try:
        # Build query filter
        query = {}
        
        # Company access control
        accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
        if company_id and company_id in accessible_company_ids:
            query["company_id"] = company_id
        else:
            query["$or"] = [
                {"company_id": {"$in": accessible_company_ids}},
                {"is_template": True}  # Public templates
            ]
        
        if layout_type:
            query["layout_type"] = layout_type
            
        # Fetch layouts
        cursor = db_service.db.content_layouts.find(query)
        layouts = await cursor.to_list(length=None)
        
        # Convert ObjectId to string
        for layout in layouts:
            layout["_id"] = str(layout["_id"])
            
        return layouts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch layouts: {str(e)}")


@router.put("/layouts/{layout_id}", response_model=Dict)
async def update_content_layout(
    layout_id: str,
    updates: ContentLayoutUpdate,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Update an existing content layout"""
    try:
        # Check layout exists and user has access
        layout = await db_service.db.content_layouts.find_one({"id": layout_id})
        if not layout:
            raise HTTPException(status_code=404, detail="Layout not found")
            
        # Check permissions
        accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
        if layout["company_id"] not in accessible_company_ids:
            raise HTTPException(status_code=403, detail="Access denied")
            
        # Update layout
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        await db_service.db.content_layouts.update_one(
            {"id": layout_id},
            {"$set": update_data}
        )
        
        return {"success": True, "message": "Layout updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update layout: {str(e)}")


# ============================================================================
# ADVERTISER CAMPAIGN MANAGEMENT  
# ============================================================================

@router.post("/campaigns", response_model=Dict)
async def create_advertiser_campaign(
    campaign: AdvertiserCampaignCreate,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new advertiser campaign"""
    try:
        # Validate user is from advertiser company
        user_companies = [c["id"] for c in company_context["accessible_companies"]]
        if campaign.advertiser_company_id not in user_companies:
            raise HTTPException(status_code=403, detail="Can only create campaigns for your company")
            
        # Validate content ownership
        content_filter = {
            "id": {"$in": campaign.content_ids},
            "status": "approved"  # Only approved content
        }
        
        content_count = await db_service.db.content_metadata.count_documents(content_filter)
        if content_count != len(campaign.content_ids):
            raise HTTPException(status_code=400, detail="Some content not found or not approved")
        
        # Create campaign
        campaign_doc = {
            **campaign.dict(),
            "id": str(uuid.uuid4()),
            "status": "draft",
            "total_impressions": 0,
            "total_clicks": 0,
            "total_spend": 0.0,
            "created_by": current_user["id"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await db_service.db.advertiser_campaigns.insert_one(campaign_doc)
        campaign_doc["_id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "campaign_id": campaign_doc["id"],
            "message": "Campaign created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")


@router.get("/campaigns", response_model=List[Dict])
async def list_advertiser_campaigns(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """List advertiser campaigns"""
    try:
        query = {}
        
        # Company access control
        accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
        if company_id and company_id in accessible_company_ids:
            query["advertiser_company_id"] = company_id
        else:
            query["advertiser_company_id"] = {"$in": accessible_company_ids}
        
        if status:
            query["status"] = status
            
        cursor = db_service.db.advertiser_campaigns.find(query)
        campaigns = await cursor.to_list(length=None)
        
        for campaign in campaigns:
            campaign["_id"] = str(campaign["_id"])
            
        return campaigns
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaigns: {str(e)}")


# ============================================================================
# CONTENT DEPLOYMENT TO DEVICES
# ============================================================================

@router.post("/deploy", response_model=Dict)
async def deploy_content_to_devices(
    deployment: ContentDeploymentCreate,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Deploy content to specific devices"""
    try:
        # Validate content access
        content = await db_service.db.content_metadata.find_one({
            "id": deployment.content_id,
            "status": "approved"
        })
        if not content:
            raise HTTPException(status_code=404, detail="Content not found or not approved")
            
        # Validate layout access
        layout = await db_service.db.content_layouts.find_one({"id": deployment.layout_id})
        if not layout:
            raise HTTPException(status_code=404, detail="Layout not found")
            
        # Validate device access
        accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
        device_query = {
            "id": {"$in": deployment.device_ids},
            "company_id": {"$in": accessible_company_ids}
        }
        
        devices_cursor = db_service.db.digital_screens.find(device_query)
        accessible_devices = await devices_cursor.to_list(length=None)
        accessible_device_ids = [d["id"] for d in accessible_devices]
        
        if len(accessible_device_ids) != len(deployment.device_ids):
            raise HTTPException(status_code=403, detail="Some devices not accessible")
        
        # Create deployment record
        deployment_doc = {
            **deployment.dict(),
            "id": str(uuid.uuid4()),
            "status": "pending",
            "deployment_progress": {device_id: "pending" for device_id in deployment.device_ids},
            "error_logs": [],
            "deployed_by": current_user["id"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        if deployment.deployment_type == "immediate":
            deployment_doc["scheduled_time"] = datetime.utcnow().isoformat()
        
        result = await db_service.db.content_deployments.insert_one(deployment_doc)
        deployment_doc["_id"] = str(result.inserted_id)
        
        # Trigger background deployment process
        background_tasks.add_task(
            process_content_deployment,
            deployment_doc["id"],
            deployment.device_ids,
            deployment.content_id,
            deployment.layout_id
        )
        
        return {
            "success": True,
            "deployment_id": deployment_doc["id"],
            "message": "Content deployment initiated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deploy content: {str(e)}")


async def process_content_deployment(deployment_id: str, device_ids: List[str], content_id: str, layout_id: str):
    """Background task to process content deployment"""
    try:
        # Update deployment status
        await db_service.db.content_deployments.update_one(
            {"id": deployment_id},
            {"$set": {"status": "deploying"}}
        )
        
        # Send deployment commands to each device
        for device_id in device_ids:
            try:
                # Update device content configuration
                await update_device_content_config(device_id, content_id, layout_id)
                
                # Mark device as deployed
                await db_service.db.content_deployments.update_one(
                    {"id": deployment_id},
                    {"$set": {f"deployment_progress.{device_id}": "deployed"}}
                )
                
            except Exception as device_error:
                # Log device-specific error
                await db_service.db.content_deployments.update_one(
                    {"id": deployment_id},
                    {
                        "$set": {f"deployment_progress.{device_id}": "failed"},
                        "$push": {"error_logs": {
                            "device_id": device_id,
                            "error": str(device_error),
                            "timestamp": datetime.utcnow().isoformat()
                        }}
                    }
                )
        
        # Update overall deployment status
        deployment = await db_service.db.content_deployments.find_one({"id": deployment_id})
        progress = deployment.get("deployment_progress", {})
        
        if all(status == "deployed" for status in progress.values()):
            final_status = "deployed"
        elif any(status == "failed" for status in progress.values()):
            final_status = "partial"
        else:
            final_status = "failed"
            
        await db_service.db.content_deployments.update_one(
            {"id": deployment_id},
            {
                "$set": {
                    "status": final_status,
                    "deployed_at": datetime.utcnow().isoformat()
                }
            }
        )
        
    except Exception as e:
        await db_service.db.content_deployments.update_one(
            {"id": deployment_id},
            {"$set": {"status": "failed"}}
        )


async def update_device_content_config(device_id: str, content_id: str, layout_id: str):
    """Update device content configuration"""
    # This would integrate with your device management system
    # For now, we'll update the device record in the database
    
    config_update = {
        "current_content_id": content_id,
        "current_layout_id": layout_id,
        "last_updated": datetime.utcnow().isoformat(),
        "sync_required": True
    }
    
    await db_service.db.digital_screens.update_one(
        {"id": device_id},
        {"$set": config_update}
    )


# ============================================================================
# ANALYTICS AND STATISTICS
# ============================================================================

@router.post("/analytics/record", response_model=Dict)
async def record_device_analytics(
    analytics: DeviceAnalytics,
    current_user=Depends(get_current_user)
):
    """Record analytics data from devices"""
    try:
        # Validate device exists
        device = await db_service.db.digital_screens.find_one({"id": analytics.device_id})
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Create analytics record
        analytics_doc = {
            **analytics.dict(),
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await db_service.db.device_analytics.insert_one(analytics_doc)
        
        # Update aggregated metrics
        await update_aggregated_metrics(analytics_doc)
        
        return {"success": True, "message": "Analytics recorded"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record analytics: {str(e)}")


@router.post("/analytics/proximity", response_model=Dict)
async def record_proximity_detection(
    proximity: ProximityDetection,
    current_user=Depends(get_current_user)
):
    """Record privacy-compliant proximity detection data"""
    try:
        # Ensure data is anonymized
        proximity_doc = {
            **proximity.dict(),
            "id": str(uuid.uuid4()),
            "data_anonymized": True,  # Force anonymization
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Remove any potentially identifying information
        if "individual_data" in proximity_doc:
            del proximity_doc["individual_data"]
        
        await db_service.db.proximity_detections.insert_one(proximity_doc)
        
        return {"success": True, "message": "Proximity data recorded"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record proximity data: {str(e)}")


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    query: AnalyticsQuery,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get analytics summary with filtering"""
    try:
        # Build aggregation pipeline
        match_stage = {}
        
        # Time filtering
        if query.start_date:
            match_stage["timestamp"] = {"$gte": query.start_date.isoformat()}
        if query.end_date:
            if "timestamp" not in match_stage:
                match_stage["timestamp"] = {}
            match_stage["timestamp"]["$lte"] = query.end_date.isoformat()
        
        # Device filtering (with access control)
        accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
        if query.device_ids:
            # Validate device access
            device_query = {
                "id": {"$in": query.device_ids},
                "company_id": {"$in": accessible_company_ids}
            }
            devices_cursor = db_service.db.digital_screens.find(device_query)
            accessible_devices = await devices_cursor.to_list(length=None)
            accessible_device_ids = [d["id"] for d in accessible_devices]
            match_stage["device_id"] = {"$in": accessible_device_ids}
        else:
            # Get all accessible devices
            devices_cursor = db_service.db.digital_screens.find({"company_id": {"$in": accessible_company_ids}})
            accessible_devices = await devices_cursor.to_list(length=None)
            accessible_device_ids = [d["id"] for d in accessible_devices]
            match_stage["device_id"] = {"$in": accessible_device_ids}
        
        # Content filtering
        if query.content_ids:
            match_stage["content_id"] = {"$in": query.content_ids}
        
        # Event type filtering
        if query.event_types:
            match_stage["event_type"] = {"$in": query.event_types}
        
        # Aggregation pipeline
        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": None,
                    "total_impressions": {
                        "$sum": {"$cond": [{"$eq": ["$event_type", "impression"]}, 1, 0]}
                    },
                    "total_revenue": {"$sum": "$estimated_revenue"},
                    "total_interactions": {
                        "$sum": {"$cond": [{"$eq": ["$event_type", "interaction"]}, 1, 0]}
                    },
                    "unique_devices": {"$addToSet": "$device_id"},
                    "avg_engagement_time": {"$avg": "$duration_seconds"}
                }
            }
        ]
        
        cursor = db_service.db.device_analytics.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        if result:
            summary_data = result[0]
            summary_data["unique_devices"] = len(summary_data.get("unique_devices", []))
        else:
            summary_data = {
                "total_impressions": 0,
                "total_revenue": 0.0,
                "total_interactions": 0,
                "unique_devices": 0,
                "avg_engagement_time": 0.0
            }
        
        # Get top performing content
        top_content_pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$content_id",
                "impressions": {"$sum": {"$cond": [{"$eq": ["$event_type", "impression"]}, 1, 0]}},
                "revenue": {"$sum": "$estimated_revenue"}
            }},
            {"$sort": {"impressions": -1}},
            {"$limit": 5}
        ]
        
        top_content_cursor = db_service.db.device_analytics.aggregate(top_content_pipeline)
        top_content = await top_content_cursor.to_list(length=5)
        
        return AnalyticsSummary(
            **summary_data,
            top_performing_content=top_content,
            revenue_by_category={},  # TODO: Implement category breakdown
            hourly_breakdown=[]  # TODO: Implement hourly breakdown
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")


async def update_aggregated_metrics(analytics_doc: Dict):
    """Update aggregated metrics for faster querying"""
    try:
        # Create daily aggregation key
        timestamp = datetime.fromisoformat(analytics_doc["timestamp"].replace("Z", "+00:00"))
        date_key = timestamp.date().isoformat()
        hour_key = timestamp.hour
        
        # Update daily metrics
        daily_key = f"{analytics_doc['device_id']}_{analytics_doc['content_id']}_{date_key}"
        
        update_data = {
            "device_id": analytics_doc["device_id"],
            "content_id": analytics_doc["content_id"],
            "date": date_key,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Increment counters based on event type
        if analytics_doc["event_type"] == "impression":
            update_data["$inc"] = {"impressions": 1}
        elif analytics_doc["event_type"] == "interaction":
            update_data["$inc"] = {"interactions": 1}
        elif analytics_doc["event_type"] == "completion":
            update_data["$inc"] = {"completions": 1}
        
        # Add revenue if present
        if analytics_doc.get("estimated_revenue", 0) > 0:
            if "$inc" not in update_data:
                update_data["$inc"] = {}
            update_data["$inc"]["revenue"] = analytics_doc["estimated_revenue"]
        
        await db_service.db.daily_metrics.update_one(
            {"id": daily_key},
            {"$set": update_data, "$inc": update_data.get("$inc", {})},
            upsert=True
        )
        
    except Exception as e:
        print(f"Failed to update aggregated metrics: {e}")


# ============================================================================
# AD CATEGORY PREFERENCES
# ============================================================================

@router.post("/ad-preferences", response_model=Dict)
async def create_ad_category_preference(
    preference: Dict,  # AdCategoryPreference data
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create ad category preferences for host companies"""
    try:
        # Validate user is from a host company
        accessible_companies = company_context["accessible_companies"]
        host_companies = [c for c in accessible_companies if c.get("type") == "HOST"]
        
        if not host_companies:
            raise HTTPException(status_code=403, detail="Only host companies can set ad preferences")
        
        # Create preference document
        preference_doc = {
            **preference,
            "id": str(uuid.uuid4()),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await db_service.db.ad_category_preferences.insert_one(preference_doc)
        
        return {
            "success": True,
            "preference_id": preference_doc["id"],
            "message": "Ad preferences created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ad preferences: {str(e)}")
