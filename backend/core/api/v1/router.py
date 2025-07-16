from fastapi import APIRouter

from .transcription import router as transcription_router

router = APIRouter(prefix="/v1", tags=["v1"])

router.include_router(transcription_router)
