import asyncio

from fastapi import APIRouter, Depends, UploadFile
from openai.types.audio import TranscriptionVerbose

from ...clients import get_openai_async_client
from ...intelligence.sound import AudioSense

router = APIRouter(prefix="/transcription", tags=["transcription"])


@router.post("/")
async def transcribe(
    audio_file: UploadFile, async_openai_client=Depends(get_openai_async_client)
) -> list[TranscriptionVerbose]:
    audio_sense = AudioSense(intelligence_client=async_openai_client)
    # compare chunked and single transcription
    # chunk_size_ms = 1000 * 60 * 10
    speed_up_factors = [1.0, 1.5, 2.0, 2.5, 3.0]
    transcriptions = await asyncio.gather(
        *[
            audio_sense.transcribe(
                audio_file=audio_file, speed_up_factor=speed_up_factor
            )
            for speed_up_factor in speed_up_factors
        ]
    )
    with open("logs/transcription.txt", "w") as f:
        for speed_up_factor, transcription in zip(speed_up_factors, transcriptions):
            transcription_text = "\n".join([t.text for t in transcription])
            f.write(f"speed_up_factor: {speed_up_factor}\n")
            f.write(f"transcription: {transcription_text}\n")
            f.write("\n")
    # for t in transcription:
    #     pprint(t.model_dump(), indent=4)
    return transcriptions
