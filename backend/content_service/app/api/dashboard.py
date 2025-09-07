from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.repo import repo
from app.auth_service import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(current_user = Depends(get_current_user)):
    """Get dashboard statistics for the current user"""
    
    try:
        # Get real data from database with error handling for missing methods
        if current_user.user_type == "SUPER_USER":
            # For SUPER_USER, show aggregated stats across all companies
            companies = await repo.list_companies() if hasattr(repo, 'list_companies') else []
            content_items = await repo.list_content_meta() if hasattr(repo, 'list_content_meta') else []
            reviews = await repo.list_reviews() if hasattr(repo, 'list_reviews') else []
            
            # Try to get digital screens if method exists, otherwise use empty list
            try:
                digital_screens = await repo.list_digital_screens() if hasattr(repo, 'list_digital_screens') else []
            except Exception:
                digital_screens = []
            
            # Calculate real stats
            stats = {
                "totalContent": len(content_items),
                "pendingApprovals": len([r for r in reviews if r.get("status") == "pending"]),
                "activeScreens": len([s for s in digital_screens if s.get("status") == "online"]),
                "totalImpressions": sum(content.get("view_count", 0) for content in content_items)
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
                    
                    stats = {
                        "totalContent": len(company_content),
                        "pendingApprovals": len(company_reviews),
                        "activeScreens": len([s for s in company_screens if s.get("status") == "online"]),
                        "totalImpressions": sum(content.get("view_count", 0) for content in company_content)
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
