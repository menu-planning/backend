from fastapi import APIRouter

from .create import router as create_router
from .delete import router as delete_router
from .fetch import router as fetch_router
from .get_by_id import router as get_by_id_router
from .rate import router as rate_router
from .update import router as update_router

router = APIRouter()

route_order = [
    create_router,
    delete_router,
    fetch_router,
    get_by_id_router,
    rate_router,
    update_router,
]

for r in route_order:
    router.include_router(r)
