from enum import Enum
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any


def create_success_response(data: Any, status_code: int = 200) -> JSONResponse:
    """Create standardized success response."""
    return JSONResponse(
        status_code=status_code,
        content={"data": data}
    )


def create_paginated_response(
    data: list[Any], 
    total: int, 
    page: int = 1, 
    limit: int = 50
) -> JSONResponse:
    """Create paginated response."""
    return JSONResponse(
        status_code=200,
        content={
            "data": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit,
            }
        }
    )

def create_router(prefix: str = "", tags: list[str | Enum] | None = None) -> APIRouter:
    """Create APIRouter with common configuration."""
    return APIRouter(prefix=prefix, tags=tags)
