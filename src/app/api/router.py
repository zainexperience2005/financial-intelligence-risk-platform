from fastapi import APIRouter

from app.api.routes.actions import (
    router as actions_router,
)
from app.api.routes.approvals import (
    router as approvals_router,
)
from app.api.routes.charts import (
    router as charts_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.investigations import (
    router as investigations_router,
)
from app.api.routes.memory import (
    router as memory_router,
)

api_router = APIRouter()

api_router.include_router(
    health_router,
)

api_router.include_router(
    investigations_router,
)

api_router.include_router(
    approvals_router,
)

api_router.include_router(
    actions_router,
)

api_router.include_router(
    memory_router,
)

api_router.include_router(
    charts_router,
)
