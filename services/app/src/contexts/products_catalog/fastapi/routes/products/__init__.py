from fastapi import APIRouter

from .create import router as create_router
from .fetch import router as fetch_router
from .get_by_id import router as get_by_id_router
from .search_similar_names import router as search_similar_names_router

router = APIRouter()

order = [
    create_router,
    fetch_router,
    get_by_id_router,
    search_similar_names_router,
]

for r in order:
    router.include_router(r)
