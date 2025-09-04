# package

from fastapi import APIRouter
from .uploads import router as uploads_router
from .auth import router as auth_router
from app.routes.content import router as content_router
from .moderation import router as moderation_router
from .companies import router as companies_router
from .users import router as users_router
# from .roles import router as roles_router  # Temporarily disabled
from .events import router as events_router
from .registration import router as registration_router
from .screens import router as screens_router
from .company_applications import router as company_applications_router
from .device import router as device_router
from .categories import router as categories_router
from .websocket import router as websocket_router
from .debug_roles import router as debug_router

# Import debug token router
from .debug_token import router as debug_token_router

# Import overlays router
from .overlays import router as overlays_router

# Import simple screens router
from .simple_screens import router as simple_screens_router

# Import content delivery router if available
try:
    from .content_delivery import router as content_delivery_router
    CONTENT_DELIVERY_ROUTER_AVAILABLE = True
except (ImportError, TypeError) as e:
    CONTENT_DELIVERY_ROUTER_AVAILABLE = False
    logger = __import__('logging').getLogger(__name__)
    logger.warning(f"Content delivery router not available: {e}")

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
from .temp_auth import router as temp_auth_router

# Import debug config router
from .debug_config import router as debug_config_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(registration_router)
api_router.include_router(uploads_router)
api_router.include_router(content_router, prefix="/content")
api_router.include_router(moderation_router)
api_router.include_router(companies_router)
api_router.include_router(users_router)
# api_router.include_router(roles_router)  # Temporarily disabled
api_router.include_router(events_router)
api_router.include_router(screens_router, prefix="/screens")
api_router.include_router(company_applications_router)
api_router.include_router(device_router)
api_router.include_router(categories_router)
api_router.include_router(websocket_router)
api_router.include_router(debug_router)
api_router.include_router(debug_token_router)
api_router.include_router(overlays_router, prefix="/overlays")
# api_router.include_router(simple_screens_router, prefix="/screens")  # Disabled - conflicts with main screens router
api_router.include_router(analytics_router)
api_router.include_router(dashboard_router)
api_router.include_router(seed_router)
api_router.include_router(temp_auth_router, prefix="/temp-auth")
api_router.include_router(debug_config_router, prefix="/debug")

# Include content delivery router if available
if CONTENT_DELIVERY_ROUTER_AVAILABLE:
    api_router.include_router(content_delivery_router)

# Include delivery router if available
if DELIVERY_ROUTER_AVAILABLE:
    api_router.include_router(delivery_router, prefix="/delivery")
