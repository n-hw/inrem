from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import configure_logging, configure_sentry
from app.api.v1 import api_v1_router
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services import notification_service

# Install structured (JSON) logging before anything else runs so module-
# import logs are already shaped correctly. Sentry only initializes when
# SENTRY_DSN is set (otherwise no-op).
configure_logging(level=settings.LOG_LEVEL)
configure_sentry(settings.SENTRY_DSN)


def _cors_origins() -> list[str]:
    """Parse CORS_ALLOW_ORIGINS env. Empty → dev-safe localhost defaults."""
    raw = (settings.CORS_ALLOW_ORIGINS or "").strip()
    if not raw:
        # Dev safety net — Expo / RN bundlers + local web preview + QA static.
        return [
            "http://localhost:8081",
            "http://localhost:19006",
            "http://localhost:3000",
            "http://localhost:8090",
        ]
    return [o.strip() for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    notification_service.initialize_notification_provider()  # fail-fast in prod
    await start_scheduler()
    yield
    await stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include API routes
app.include_router(api_v1_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to InRem API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
