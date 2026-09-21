from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.middleware import RequestIDMiddleware
from app.api.router import api_router
from app.core.exceptions import ApplicationError
from app.graphs.financial_graph import build_financial_graph
from kit.config import get_settings
from kit.graphs.checkpointing import create_postgres_checkpointer

ERROR_STATUS_CODES = {
    "resource_not_found": 404,
    "action_not_allowed": 403,
    "investigation_failed": 422,
    "conflict": 409,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with create_postgres_checkpointer() as checkpointer:
            checkpointer.setup()
            app.state.financial_graph = build_financial_graph(checkpointer=checkpointer)
            yield
    except Exception:
        # Fallback if checkpoint database is unavailable
        app.state.financial_graph = build_financial_graph()
        yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)


@app.exception_handler(ApplicationError)
async def application_error_handler(
    request: Request,
    exc: ApplicationError,
):
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )
    status_code = ERROR_STATUS_CODES.get(
        exc.code,
        400,
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.code,
            "message": exc.message,
            "request_id": request_id,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            "request_id": request_id,
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    exc: Exception,
):
    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
            "request_id": request_id,
        },
    )


app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} API is running"}
