"""FastAPI routers for IAM context."""

from .user import router as user_router

__all__ = [
    "user_router",
]
