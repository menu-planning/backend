"""FastAPI routers for client onboarding context."""

from .form_create import router as form_create_router
from .form_update import router as form_update_router
from .form_delete import router as form_delete_router
from .webhook_process import router as webhook_process_router
from .query_responses import router as query_responses_router
from .bulk_query_responses import router as bulk_query_responses_router

# Combine all client onboarding routers
from fastapi import APIRouter

router = APIRouter()
router.include_router(form_create_router)
router.include_router(form_update_router)
router.include_router(form_delete_router)
router.include_router(webhook_process_router)
router.include_router(query_responses_router)
router.include_router(bulk_query_responses_router)

__all__ = ["router"]
