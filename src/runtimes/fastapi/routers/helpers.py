import json

from enum import Enum
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Any



def create_success_response(data: Any, status_code: int = 200) -> JSONResponse:
    """Create standardized success response."""
    if isinstance(data, str):
        data = json.loads(data)
    return JSONResponse(
        status_code=status_code,
        content={"data": data}
    )


def create_paginated_response(
    data: Any, 
    total: int, 
    page: int = 1, 
    limit: int = 50
) -> JSONResponse:
    """Create paginated response."""
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, bytes):
        data = data.decode("utf-8")
        data = json.loads(data)
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
