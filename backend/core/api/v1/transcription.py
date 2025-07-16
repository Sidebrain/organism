from fastapi import APIRouter, Depends, UploadFile
from openai.types.audio import TranscriptionVerbose

from ...clients import get_openai_async_client
from ...intelligence.sound import AudioSense

router = APIRouter(prefix="/transcription", tags=["transcription"])


@router.post("/")
async def transcribe(
    audio_file: UploadFile,
    async_openai_client=Depends(get_openai_async_client),
) -> list[TranscriptionVerbose]:
    audio_sense = AudioSense(intelligence_client=async_openai_client)
    transcription = await audio_sense.transcribe(audio_file=audio_file)
    return transcription
