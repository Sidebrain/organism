from fastapi import APIRouter, Depends, UploadFile
from openai.types.audio import Transcription, TranscriptionVerbose

from core.intelligence.extractor import Extractor

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
    if transcription is None:
        return []

    transcription_text = [t.text for t in transcription]

    extractor = Extractor()
    extracted_entities = await extractor.base_extraction("\n".join(transcription_text))

    with open("logs/extracted_entities.json", "a+") as f:
        json_str = [e.model_dump_json() for e in extracted_entities if e is not None]
        f.write("\n".join(json_str))

    return transcription
