from fastapi import APIRouter

from .add_receipt import router as add_receipt_router
from .change_name import router as change_name_router
from .create import router as create_router
from .discard import router as discard_router
from .fetch import router as fetch_router
from .fetch_houses_user_is_member import router as fetch_houses_user_is_member_router
from .fetch_houses_user_is_nutritionist import (
    router as fetch_houses_user_is_nutritionist_router,
)
from .fetch_houses_user_own import router as fetch_houses_user_own_router
from .get_by_id import router as get_by_id_router
from .invite_member import router as invite_member_router
from .invite_nutritionist import router as invite_nutritionist_router
from .remove_member import router as remove_member_router
from .remove_nutritionist import router as remove_nutritionist_router

router = APIRouter()

route_order = [
    fetch_router,
    create_router,
    discard_router,
    fetch_houses_user_own_router,
    fetch_houses_user_is_member_router,
    fetch_houses_user_is_nutritionist_router,
    invite_member_router,
    invite_nutritionist_router,
    remove_member_router,
    remove_nutritionist_router,
    add_receipt_router,
    change_name_router,
    get_by_id_router,
]

for r in route_order:
    router.include_router(r)
