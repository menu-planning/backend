from fastapi import APIRouter

from .add import router as add_router
from .discard_from_house import router as discard_router
from .fetch_house_items import router as fetch_router
from .get_by_id import router as get_by_id_router
from .update import router as update_router

router = APIRouter()

route_order = [
    add_router,
    discard_router,
    fetch_router,
    update_router,
    get_by_id_router,
]

for r in route_order:
    router.include_router(r)
