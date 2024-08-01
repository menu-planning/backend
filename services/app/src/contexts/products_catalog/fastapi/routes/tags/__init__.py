from fastapi import APIRouter

from .create import router as create_router
from .delete import router as delete_router
from .fetch import router as fetch_router
from .get_by_id import router as get_by_id_router

router = APIRouter()

order = [
    create_router,
    delete_router,
    fetch_router,
    get_by_id_router,
]

for route in order:
    router.include_router(route)
