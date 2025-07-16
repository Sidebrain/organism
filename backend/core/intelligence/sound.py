import asyncio
import io

from fastapi import UploadFile
from openai import AsyncOpenAI
from openai.types.audio import TranscriptionVerbose
from pydub import AudioSegment  # type: ignore
from pydub.effects import speedup  # type: ignore

from core.utils import time_it


class AudioSense:
    def __init__(self, intelligence_client: AsyncOpenAI) -> None:
        self.intelligence_client = intelligence_client

    @time_it
    async def transcribe(
        self,
        audio_file: UploadFile,
        chunk_size_ms: int | None = None,
        speed_up_factor: float = 1.0,
    ) -> list[TranscriptionVerbose]:
        audio_file.file.seek(0)
        audio = AudioSegment.from_file(audio_file.file)
        if speed_up_factor != 1.0:
            audio = speedup(audio, speed_up_factor)

        if chunk_size_ms is None:
            chunk_size_ms = len(audio)

        segments = [
            audio[i : i + chunk_size_ms] for i in range(0, len(audio), chunk_size_ms)
        ]

        transcription_segments = await asyncio.gather(
            *[
                self.transcribe_segment(segment, audio_file, index)
                for index, segment in enumerate(segments)
            ]
        )

        return [
            transcription_segment
            for _, transcription_segment in sorted(
                transcription_segments, key=lambda x: x[0]
            )
        ]

    @time_it
    async def transcribe_segment(
        self, segment: AudioSegment, original_audio_file: UploadFile, index: int
    ) -> tuple[int, TranscriptionVerbose]:
        buffer = io.BytesIO()
        segment.export(buffer, format="mp3")
        buffer.seek(0)
        file_tuple = (
            original_audio_file.filename,
            buffer,
            # original_audio_file.content_type,
            "audio/mp3",
        )
        return index, await self.intelligence_client.audio.transcriptions.create(
            file=file_tuple,
            model="whisper-1",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
