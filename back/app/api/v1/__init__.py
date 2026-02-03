from fastapi import APIRouter

from .auth import router as auth_router
from .signal import router as signal_router
from .device import router as device_router
from .pulse import router as pulse_router
from .guardian import router as guardian_router
from .settings import router as settings_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(signal_router)
api_v1_router.include_router(device_router)
api_v1_router.include_router(pulse_router)
api_v1_router.include_router(guardian_router)
api_v1_router.include_router(settings_router)
