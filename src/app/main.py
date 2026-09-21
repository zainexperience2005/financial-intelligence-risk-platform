from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.actions import router as actions_router
from app.api.approvals import router as approvals_router
from app.api.routes import router
from app.graphs.financial_graph import build_financial_graph
from kit.config import get_settings
from kit.graphs.checkpointing import create_postgres_checkpointer


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

app.include_router(router)
app.include_router(approvals_router)
app.include_router(actions_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} API is running"}
