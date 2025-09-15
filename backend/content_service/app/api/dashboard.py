from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
from app.repo import repo
from app.api.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(current_user = Depends(get_current_user)):
    """Get real dashboard statistics for the current user using aggregated data"""
    
    try:
        # Import analytics service for real-time data
        from app.analytics.real_time_analytics import analytics_service
        
        # Get real data from database with error handling for missing methods
        if current_user.user_type == "SUPER_USER":
            # For SUPER_USER, show aggregated stats across all companies
            companies = await repo.list_companies() if hasattr(repo, 'list_companies') else []
            content_items = await repo.list_content_meta() if hasattr(repo, 'list_content_meta') else []
            reviews = await repo.list_reviews() if hasattr(repo, 'list_reviews') else []
            
            # Get digital screens with error handling
            try:
                digital_screens = await repo.list_digital_screens() if hasattr(repo, 'list_digital_screens') else []
            except Exception:
                digital_screens = []
            
            # Get real-time analytics data
            try:
                analytics_data = await analytics_service.get_dashboard_data(
                    device_filter=None,
                    start_time=datetime.utcnow() - timedelta(hours=24),
                    end_time=datetime.utcnow()
                )
                total_impressions = analytics_data.get("summary", {}).get("totalImpressions", 0)
                online_screens = analytics_data.get("summary", {}).get("onlineDevices", 0)
            except Exception as e:
                # Fallback if analytics service fails
                total_impressions = sum(content.get("view_count", 0) for content in content_items)
                online_screens = len([s for s in digital_screens if s.get("status") == "online"])
            
            # Calculate real stats
            stats = {
                "totalContent": len(content_items),
                "pendingApprovals": len([r for r in reviews if r.get("status") == "pending"]),
                "activeScreens": online_screens,
                "totalImpressions": total_impressions
            }
        else:
            # For regular users, show their company stats
            user_company_id = current_user.company_id
            if user_company_id:
                company = await repo.get_company(user_company_id) if hasattr(repo, 'get_company') else None
                if company:
                    # Get company-specific data with error handling
                    try:
                        # Try to get company screens if method exists
                        if hasattr(repo, 'list_digital_screens'):
                            company_screens = await repo.list_digital_screens()
                            # Filter by company_id if the screens have that field
                            company_screens = [s for s in company_screens if s.get("company_id") == user_company_id]
                        else:
                            company_screens = []
                    except Exception:
                        company_screens = []
                    
                    # Get content and reviews
                    content_items = await repo.list_content_meta() if hasattr(repo, 'list_content_meta') else []
                    reviews = await repo.list_reviews() if hasattr(repo, 'list_reviews') else []
                    
                    # Filter content by company (if content has company_id field)
                    company_content = [c for c in content_items if c.get("company_id") == user_company_id]
                    company_reviews = [r for r in reviews if r.get("company_id") == user_company_id and r.get("status") == "pending"]
                    
                    # Get real-time analytics for this company
                    try:
                        # Get device IDs for this company
                        company_device_ids = [s.get("id") or s.get("device_id") for s in company_screens if s.get("id") or s.get("device_id")]
                        
                        if company_device_ids:
                            # Get analytics for company devices
                            analytics_data = await analytics_service.get_dashboard_data(
                                device_filter=None,  # We'll filter by company devices
                                start_time=datetime.utcnow() - timedelta(hours=24),
                                end_time=datetime.utcnow()
                            )
                            
                            # Filter analytics data for company devices
                            company_analytics = {
                                "devices": [d for d in analytics_data.get("devices", []) if d.get("deviceId") in company_device_ids],
                                "summary": analytics_data.get("summary", {})
                            }
                            
                            # Calculate company-specific metrics
                            company_impressions = sum(d.get("contentMetrics", {}).get("impressions", 0) for d in company_analytics["devices"])
                            company_online_screens = len([d for d in company_analytics["devices"] if d.get("isOnline", False)])
                        else:
                            company_impressions = sum(content.get("view_count", 0) for content in company_content)
                            company_online_screens = len([s for s in company_screens if s.get("status") == "online"])
                    except Exception as e:
                        # Fallback to basic calculations
                        company_impressions = sum(content.get("view_count", 0) for content in company_content)
                        company_online_screens = len([s for s in company_screens if s.get("status") == "online"])
                    
                    stats = {
                        "totalContent": len(company_content),
                        "pendingApprovals": len(company_reviews),
                        "activeScreens": company_online_screens,
                        "totalImpressions": company_impressions
                    }
                else:
                    stats = {
                        "totalContent": 0,
                        "pendingApprovals": 0,
                        "activeScreens": 0,
                        "totalImpressions": 0
                    }
            else:
                stats = {
                    "totalContent": 0,
                    "pendingApprovals": 0,
                    "activeScreens": 0,
                    "totalImpressions": 0
                }
        
        # Return stats directly (not nested in a "stats" object)
        return stats
        
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Dashboard stats error: {str(e)}", exc_info=True)
        
        # Return default stats instead of failing
        return {
            "totalContent": 0,
            "pendingApprovals": 0,
            "activeScreens": 0,
            "totalImpressions": 0
        }
