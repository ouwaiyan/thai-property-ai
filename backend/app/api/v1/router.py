from fastapi import APIRouter

from app.api.v1.ai import router as ai_router
from app.api.v1.api_settings import router as api_settings_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.geo import router as geo_router
from app.api.v1.imports import router as imports_router
from app.api.v1.leads import router as leads_router
from app.api.v1.line import router as line_router
from app.api.v1.line_rich_menu import router as line_rich_menu_router
from app.api.v1.n8n import router as n8n_router
from app.api.v1.reports import router as reports_router
from app.api.v1.properties import router as properties_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.transit import router as transit_router
from app.api.v1.users import router as users_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(properties_router)
api_v1_router.include_router(audit_logs_router)
api_v1_router.include_router(imports_router)
api_v1_router.include_router(geo_router)
api_v1_router.include_router(transit_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(leads_router)
api_v1_router.include_router(line_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(n8n_router)
api_v1_router.include_router(line_rich_menu_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(api_settings_router)
