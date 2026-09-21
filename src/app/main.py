from fastapi import FastAPI

from app.api.routes import router
from kit.config import get_settings

settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": f"{settings.app_name} API is running"}
