from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import api_v1_router
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    # Startup
    await start_scheduler()
    yield
    # Shutdown
    await stop_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

# Include API routes
app.include_router(api_v1_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to InRem API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
