"""
FastAPI lifespan management with anyio task supervision.

This module provides lifespan management for FastAPI applications using anyio
for task supervision and concurrency control.
"""

from contextlib import asynccontextmanager
from typing import Coroutine, Any, Optional
import logging

import anyio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.app_config import get_app_settings
from src.runtimes.fastapi.dependencies.containers import AppContainer

from src.runtimes.fastapi.error_handling import setup_error_handlers
from src.runtimes.fastapi.routers.client_onboarding import router as client_onboarding_router
from src.runtimes.fastapi.routers.health import router as health_router
from src.runtimes.fastapi.routers.iam import user_router as iam_user_router
from src.runtimes.fastapi.routers.products_catalog import router as products_router
from src.runtimes.fastapi.routers.recipes_catalog import (
    client_router,
    meal_router,
    recipe_router,
    menu_view_router,
    tag_router,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager with anyio task supervision.
    
    This lifespan manager:
    - Creates a task group for supervised background tasks
    - Provides a spawn function with proper exception handling
    - Sets up capacity limiter for concurrency control
    - Handles graceful shutdown with spawn rejection
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None: Application is ready to handle requests
    """
    container = AppContainer()
    app.state.container = container
    
    async with anyio.create_task_group() as tg:
        app.state.bg_limiter = anyio.CapacityLimiter(64)

        async def _supervise(coro: Coroutine[Any, Any, Any], *, name: Optional[str] = None):
            """Supervise background tasks with proper exception handling."""
            try:
                await coro
            except anyio.get_cancelled_exc_class():
                logger.info("BG task cancelled", extra={"task": name})
                raise
            except BaseException:
                logger.exception("BG task crashed", extra={"task": name})
                # swallow so TG isn't cancelled by faults

        def spawn(coro: Coroutine[Any, Any, Any], *, name: Optional[str] = None) -> None:
            """Spawn a supervised background task."""
            tg.start_soon(_supervise, coro, name=name)

        app.state.spawn = spawn

        # Get app configuration
        config = get_app_settings()
        app.state.config = config

        logger.info("FastAPI application starting with task supervision")

        try:
            yield
        finally:
            # Block late spawns during shutdown (optional hygiene)
            def _reject_spawn(_: Coroutine[Any, Any, Any], *, name: Optional[str] = None):
                logger.warning("Spawn called during shutdown", extra={"task": name})
                raise RuntimeError("Shutting down")
            app.state.spawn = _reject_spawn

            # tiny grace before TG auto-cancels/joins children
            with anyio.move_on_after(0.2):
                await anyio.sleep(0)

            logger.info("FastAPI application shutdown complete")


def create_app() -> FastAPI:
    """Create FastAPI application with lifespan management.
    
    Returns:
        FastAPI application instance with lifespan
    """
    config = get_app_settings()
    
    app = FastAPI(
        title="Menu Planning API",
        description="FastAPI runtime for Menu Planning application",
        version="1.0.0",
        lifespan=lifespan,
        docs_url=config.fastapi_docs_url,
        redoc_url=config.fastapi_redoc_url,
        openapi_url=config.fastapi_openapi_url,
    )
    
    # Configure OpenAPI security schemes for Swagger UI integration
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        from fastapi.openapi.utils import get_openapi
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Add security scheme to OpenAPI spec
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token from Cognito authentication"
            }
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.fastapi_cors_origins,
        allow_credentials=config.fastapi_cors_allow_credentials,
        allow_methods=config.fastapi_cors_allow_methods,
        allow_headers=config.fastapi_cors_allow_headers,
    )
    
    # Setup error handlers (native FastAPI approach)
    setup_error_handlers(app)
   
    # Include routers with context-level tags for auth middleware
    app.include_router(health_router)
    
    # Products catalog context
    app.include_router(products_router, tags=["products_catalog"])
    
    # Client onboarding context
    app.include_router(client_onboarding_router, tags=["client_onboarding"])
    
    # Recipes catalog context
    app.include_router(recipe_router, tags=["recipes_catalog"])
    app.include_router(meal_router, tags=["recipes_catalog"])
    app.include_router(client_router, tags=["recipes_catalog"])
    app.include_router(tag_router, tags=["recipes_catalog"])
    app.include_router(menu_view_router, tags=["recipes_catalog"])
    
    # IAM context
    app.include_router(iam_user_router, tags=["iam"])
    
    return app

app = create_app()
