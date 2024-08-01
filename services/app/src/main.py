from contextlib import asynccontextmanager
from typing import AsyncContextManager

# import firebase_admin
from anyio import CapacityLimiter, lowlevel
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.api.api_v1 import api
from src.config.api_config import get_api_settings
from src.config.app_config import get_app_settings
from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.logging.logger import LoggerFactory, logger
from starlette.middleware.cors import CORSMiddleware

# from .config.logging_config import get_log_settings

LoggerFactory.configure(logger_name="app-server")
logger.info("Starting server")


def create_app(lifespan: AsyncContextManager) -> FastAPI:
    app_settings = get_app_settings()
    api_settings = get_api_settings()

    # if os.getenv("APP_CONFIG") != "testing":
    #     if log_settings := get_log_settings():
    #         dictConfig(log_settings.model_dump())

    openapi_url = "{}{}".format(api_settings.openapi_prefix, api_settings.openapi_url)
    docs_url = "{}{}".format(api_settings.api_v1_str, api_settings.docs_url)
    redoc_url = "{}{}".format(api_settings.api_v1_str, api_settings.redoc_url)

    # default_app = firebase_admin.initialize_app()

    server = FastAPI(
        title=app_settings.project_name,
        openapi_url=openapi_url,
        docs_url=docs_url,
        redoc_url=redoc_url,
        debug=api_settings.debug,
    )
    server.include_router(api.api_router, prefix=api_settings.api_v1_str)

    if api_settings.backend_cors_origins:
        server.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            # allow_origins=[str(origin) for origin in api_settings.backend_cors_origins],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return server


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncContextManager:  # type: ignore
    print("Startup")
    lowlevel.RunVar("_default_thread_limiter").set(CapacityLimiter(1))
    yield
    print("Shutdown")


app = create_app(lifespan=lifespan)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"},
    )


@app.exception_handler(TimeoutError)
async def timeout_exception_handler(request: Request, exc: TimeoutError):
    return JSONResponse(
        status_code=status.HTTP_408_REQUEST_TIMEOUT,
        content={"detail": "Request processing time excedeed limit"},
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": f"Error in processing data: {exc}"},
    )


@app.exception_handler(EntityNotFoundException)
async def entity_not_found_exception_handler(
    request: Request, exc: EntityNotFoundException
):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message},
    )


@app.exception_handler(MultipleEntitiesFoundException)
async def multiple_entities_found_exception_handler(
    request: Request, exc: MultipleEntitiesFoundException
):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": exc.message},
    )


# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content={"detail": exc.errors(), "body": exc.body},
#     )
