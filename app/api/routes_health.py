from fastapi import APIRouter

from app.config import get_settings
from app.schemas.chat import HealthResponse

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse, response_model_exclude_none=True)
async def healthz() -> HealthResponse:
    settings = get_settings()
    # Open to everyone (uptime checks): only "ok". The vector store detail is for development only.
    dev = settings.app_env.lower() in {"development", "dev", "local", "test"}
    return HealthResponse(status="ok", vector_store_backend=settings.vector_store_backend if dev else None)
