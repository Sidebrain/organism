from fastapi import APIRouter

from .chat import router as chat_router
from .transcription import router as transcription_router

router = APIRouter(prefix="/v1", tags=["v1"])

router.include_router(transcription_router)
router.include_router(chat_router)
