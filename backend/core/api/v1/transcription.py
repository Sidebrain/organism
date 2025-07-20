from fastapi import APIRouter, Depends, UploadFile
from openai.types.audio import Transcription, TranscriptionVerbose

from ...clients import get_openai_async_client
from ...senses.sound import AudioSense

router = APIRouter(prefix="/transcription", tags=["transcription"])


@router.post("/")
async def transcribe(
    audio_file: UploadFile,
    async_openai_client=Depends(get_openai_async_client),
) -> list[TranscriptionVerbose | Transcription]:
    audio_sense = AudioSense(intelligence_client=async_openai_client)
    transcription = await audio_sense.transcribe(audio_file=audio_file)
    with open("logs/transcription.txt", "a") as f:
        f.write(f"gpt-4o-transcribe:\n{transcription}\n")
    return transcription
