# package

from fastapi import APIRouter
from .uploads import router as uploads_router
from .auth import router as auth_router
from app.routes.content import router as content_router
from .moderation import router as moderation_router
from .companies import router as companies_router
from .users import router as users_router
from .roles import router as roles_router
from .events import router as events_router
from .registration import router as registration_router
from .screens import router as screens_router
from .company_applications import router as company_applications_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(registration_router)
api_router.include_router(uploads_router)
api_router.include_router(content_router, prefix="/content")
api_router.include_router(moderation_router)
api_router.include_router(companies_router)
api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(events_router)
api_router.include_router(screens_router)
api_router.include_router(company_applications_router)
