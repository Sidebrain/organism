import asyncio
import io

from fastapi import UploadFile
from openai import AsyncOpenAI
from openai.types.audio import Transcription, TranscriptionVerbose
from pydub import AudioSegment  # type: ignore
from pydub.effects import speedup  # type: ignore

from core.utils import time_it

from .audio_processing import AudioExporter, AudioLoader, AudioSegmenter
from .file_handling import AudioFileHandler
from .format_detection import AudioFormatDetector
from .transcription import TranscriptionAssembler, TranscriptionProcessor


class AudioSense:
    """Main audio transcription orchestrator"""

    def __init__(self, intelligence_client: AsyncOpenAI) -> None:
        self.intelligence_client = intelligence_client
        self.format_detector = AudioFormatDetector()
        self.file_handler = AudioFileHandler()
        self.audio_loader = AudioLoader()
        self.audio_segmenter = AudioSegmenter()
        self.audio_exporter = AudioExporter()
        self.transcription_processor = TranscriptionProcessor(intelligence_client)
        self.transcription_assembler = TranscriptionAssembler()

    def __repr__(self) -> str:
        return "AudioSense(intelligence_client_wrapper_openai)"

    def apply_speed_modification(
        self, audio: AudioSegment, speed_up_factor: float
    ) -> AudioSegment:
        """Apply speed modification to audio if needed"""
        if speed_up_factor != 1.0:
            return speedup(audio, speed_up_factor)
        return audio

    async def transcribe_m4a_directly(
        self, audio_file: UploadFile
    ) -> list[TranscriptionVerbose | Transcription]:
        """Direct transcription for m4a files without re-encoding"""

        def create_direct_file_tuple(
            audio_file: UploadFile,
        ) -> tuple[str, io.BytesIO, str]:
            """Create file tuple directly from original m4a data"""
            buffer = io.BytesIO(audio_file.file.read())
            buffer.seek(0)
            return (audio_file.filename or "audio.m4a", buffer, "audio/m4a")

        file_tuple = create_direct_file_tuple(audio_file)
        transcription = await self.transcription_processor.transcribe_audio_segment(
            file_tuple
        )
        return [transcription]

    async def process_audio_segments_concurrently(
        self, segments: list[AudioSegment], detected_audio_format: str
    ) -> list[tuple[int, TranscriptionVerbose | Transcription]]:
        """Process all audio segments concurrently"""
        return await asyncio.gather(
            *[
                self.transcription_processor.process_segment_with_index(
                    segment, index, detected_audio_format, self.audio_exporter
                )
                for index, segment in enumerate(segments)
            ]
        )

    @time_it
    async def transcribe(
        self,
        audio_file: UploadFile,
        chunk_size_ms: int | None = None,
        speed_up_factor: float = 1.0,
    ) -> list[TranscriptionVerbose | Transcription]:
        """Transcribe audio file with functional pipeline"""
        reset_file = self.file_handler.reset_file_position(audio_file)
        detected_audio_format = self.format_detector.determine_audio_format(audio_file)
        self.file_handler.log_file_information(audio_file, detected_audio_format)

        # Fast path optimization for m4a files
        if self.audio_exporter.should_use_m4a_fast_path(
            detected_audio_format, speed_up_factor, audio_file.size or 0
        ):
            print("Using m4a fast path - skipping re-encoding")
            return await self.transcribe_m4a_directly(audio_file)

        # Existing pipeline for all other cases
        raw_audio = self.audio_loader.load_audio_with_fallback(
            reset_file, detected_audio_format
        )
        processed_audio = self.apply_speed_modification(raw_audio, speed_up_factor)

        optimal_chunk_size = (
            chunk_size_ms
            or self.audio_segmenter.calculate_optimal_chunk_duration(len(raw_audio))
        )
        audio_segments = self.audio_segmenter.split_audio_into_segments(
            processed_audio, optimal_chunk_size
        )
        self.audio_segmenter.log_segment_processing_info(
            audio_segments, optimal_chunk_size
        )

        transcription_segments = await self.process_audio_segments_concurrently(
            audio_segments, detected_audio_format
        )
        return self.transcription_assembler.assemble_final_transcriptions(
            transcription_segments
        )
