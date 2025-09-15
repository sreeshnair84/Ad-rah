# package

from fastapi import APIRouter
from .auth import router as auth_router
from .moderation import router as moderation_router
from .companies import router as companies_router
from .users import router as users_router
# from .roles import router as roles_router  # Temporarily disabled
from .events import router as events_router
from .registration import router as registration_router
from .company_applications import router as company_applications_router
from .categories import router as categories_router
from .websocket import router as websocket_router
from .debug_roles import router as debug_router

# Import debug token router
# from .debug_token import router as debug_token_router  # Removed - depends on removed auth service

# Import unified content management router (consolidates routes/content.py, api/content_delivery.py, api/enhanced_content.py, api/uploads.py)
from .content_unified import router as content_unified_router

# Import uploads router
from .uploads import router as uploads_router

# Import unified overlays management router (consolidates routes/overlay.py and api/overlays.py)
from .devices_unified import router as devices_unified_router
from .overlays_unified import router as overlays_unified_router

# Import digital twins router
from .digital_twins import router as digital_twins_router

# Import content delivery router if available
try:
    from .delivery import router as content_delivery_router
    CONTENT_DELIVERY_ROUTER_AVAILABLE = True
except (ImportError, TypeError) as e:
    CONTENT_DELIVERY_ROUTER_AVAILABLE = False
    # Content delivery functionality is now in content_unified.py
    print(f"Content delivery router not available (consolidated into content_unified.py): {e}")

# Import delivery router
try:
    from .delivery import router as delivery_router
    DELIVERY_ROUTER_AVAILABLE = True
except (ImportError, TypeError) as e:
    DELIVERY_ROUTER_AVAILABLE = False
    logger = __import__('logging').getLogger(__name__)
    logger.warning(f"Delivery router not available: {e}")

# Import analytics router
from .analytics import router as analytics_router

# Import dashboard router
from .dashboard import router as dashboard_router

# Import seed router for testing
from .seed import router as seed_router

# Import temp auth router for debugging
# from .temp_auth import router as temp_auth_router  # Removed - temporary debug router

# Import test seed router for testing authentication
from .test_seed import router as test_seed_router

# Import debug config router
from .debug_config import router as debug_config_router

# Import history router for content tracking
from .history import router as history_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(registration_router)
api_router.include_router(content_unified_router)  # Unified content management
api_router.include_router(uploads_router)  # Upload management
api_router.include_router(moderation_router)
api_router.include_router(companies_router)
api_router.include_router(users_router)
# api_router.include_router(roles_router)  # Temporarily disabled
api_router.include_router(events_router)
api_router.include_router(company_applications_router)
api_router.include_router(devices_unified_router)  # Unified device management (replaces device_router, screens_router, simple_screens_router)
api_router.include_router(digital_twins_router)  # Digital twin management
api_router.include_router(categories_router)
api_router.include_router(websocket_router)
api_router.include_router(debug_router)
# api_router.include_router(debug_token_router)  # Removed - depends on removed auth service
api_router.include_router(overlays_unified_router)  # Unified overlays management
api_router.include_router(analytics_router)
api_router.include_router(dashboard_router)
api_router.include_router(history_router)  # Content history and audit tracking
api_router.include_router(seed_router)
api_router.include_router(test_seed_router)  # Test seed router for authentication testing
# api_router.include_router(temp_auth_router, prefix="/temp-auth")  # Removed - temporary debug router
api_router.include_router(debug_config_router, prefix="/debug")

# Include content delivery router if available
if CONTENT_DELIVERY_ROUTER_AVAILABLE:
    api_router.include_router(content_delivery_router)

# Include delivery router if available
if DELIVERY_ROUTER_AVAILABLE:
    api_router.include_router(delivery_router, prefix="/delivery")
