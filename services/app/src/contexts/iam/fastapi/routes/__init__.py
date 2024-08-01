from fastapi import APIRouter

from .assign_role import router as assign_role_router
from .create_user import router as create_router
from .get_user_by_id import router as get_by_id_router
from .remove_role import router as remove_role_router

router = APIRouter()

order = [
    create_router,
    assign_role_router,
    remove_role_router,
    get_by_id_router,
]

for r in order:
    router.include_router(r)
