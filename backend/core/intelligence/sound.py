import asyncio
import io
import os
from pathlib import Path

from fastapi import UploadFile
from openai import AsyncOpenAI
from openai.types.audio import Transcription, TranscriptionVerbose
from pydub import AudioSegment  # type: ignore
from pydub.effects import speedup  # type: ignore

from core.utils import time_it

# Module-level constants
WHISPER_MODEL = "whisper-1"
MAX_CHUNK_DURATION_MS = 30 * 60 * 1000  # 30 minutes in milliseconds
OPTIMAL_EXPORT_FORMAT = "ogg"

SUPPORTED_AUDIO_FORMATS = [".mp3", ".mp4", ".m4a", ".wav", ".flac", ".ogg", ".webm"]


class AudioSense:
    def __init__(self, intelligence_client: AsyncOpenAI) -> None:
        self.intelligence_client = intelligence_client

    def __repr__(self) -> str:
        return "AudioSense(intelligence_client_wrapper_openai)"

    # ============================================================================
    # FILE HANDLING AND FORMAT DETECTION
    # ============================================================================

    def determine_audio_format(self, audio_file: UploadFile) -> str:
        """Determine audio format from filename or content-type with fallback"""

        def extract_audio_format_from_filename(audio_file: UploadFile) -> str | None:
            """Extract audio format from filename extension. Example: .mp3 -> mp3"""
            if not audio_file.filename:
                return None
            suffix = Path(audio_file.filename).suffix.lower()
            if suffix in SUPPORTED_AUDIO_FORMATS:
                return suffix[1:]  # Remove the dot
            return None

        def extract_audio_format_from_content_type(
            audio_file: UploadFile,
        ) -> str | None:
            """Extract audio format from content-type header"""
            if not audio_file.content_type:
                return None
            content_type = audio_file.content_type.lower()
            if "mp4" in content_type or "m4a" in content_type:
                return "m4a"
            elif "mp3" in content_type:
                return "mp3"
            elif "wav" in content_type:
                return "wav"
            return None

        format_from_filename = extract_audio_format_from_filename(audio_file)
        if format_from_filename:
            return format_from_filename

        format_from_content_type = extract_audio_format_from_content_type(audio_file)
        if format_from_content_type:
            return format_from_content_type

        return "mp3"  # Default fallback

    def reset_file_position(self, audio_file: UploadFile) -> UploadFile:
        """Reset file position to beginning"""
        audio_file.file.seek(0)
        return audio_file

    def log_file_information(self, audio_file: UploadFile, file_format: str) -> None:
        """Log file information for debugging"""

        def calculate_file_size_in_kilobytes(audio_file: UploadFile) -> float:
            """Calculate file size in kilobytes"""
            return (audio_file.size or 0) / 1024

        file_size_kb = calculate_file_size_in_kilobytes(audio_file)
        print(f"Size of audio file in {file_format} in kb: {file_size_kb}")

    # ============================================================================
    # AUDIO LOADING AND PROCESSING
    # ============================================================================

    def load_audio_with_fallback(
        self, audio_file: UploadFile, file_format: str
    ) -> AudioSegment:
        """Load audio with fallback to temporary file if direct loading fails"""

        def load_audio_from_file_object(
            audio_file: UploadFile, file_format: str
        ) -> AudioSegment:
            """Load audio directly from file object"""
            return AudioSegment.from_file(audio_file.file, format=file_format)

        def create_temporary_audio_file(
            audio_file: UploadFile, file_format: str
        ) -> str:
            """Create temporary file for audio loading fallback"""
            temp_filename = f"temp.{file_format}"
            with open(temp_filename, "wb") as f:
                f.write(audio_file.file.read())
            return temp_filename

        def load_audio_from_temporary_file(temp_filename: str) -> AudioSegment:
            """Load audio from temporary file"""
            return AudioSegment.from_file(temp_filename)

        def cleanup_temporary_file(temp_filename: str) -> None:
            """Remove temporary file"""
            os.unlink(temp_filename)

        try:
            return load_audio_from_file_object(audio_file, file_format)
        except Exception:
            temp_filename = create_temporary_audio_file(audio_file, file_format)
            audio = load_audio_from_temporary_file(temp_filename)
            cleanup_temporary_file(temp_filename)
            return audio

    def apply_speed_modification(
        self, audio: AudioSegment, speed_up_factor: float
    ) -> AudioSegment:
        """Apply speed modification to audio if needed"""
        if speed_up_factor != 1.0:
            return speedup(audio, speed_up_factor)
        return audio

    # ============================================================================
    # AUDIO SEGMENTATION AND CHUNKING
    # ============================================================================

    def calculate_optimal_chunk_duration(self, audio_duration_ms: int) -> int:
        """Calculate optimal chunk duration based on audio length and OpenAI limits"""

        if audio_duration_ms <= MAX_CHUNK_DURATION_MS:
            return audio_duration_ms

        return MAX_CHUNK_DURATION_MS

    def split_audio_into_segments(
        self, audio: AudioSegment, chunk_size_ms: int
    ) -> list[AudioSegment]:
        """Split audio into segments of specified duration"""
        return [
            audio[i : i + chunk_size_ms] for i in range(0, len(audio), chunk_size_ms)
        ]

    def log_segment_processing_info(
        self, segments: list[AudioSegment], chunk_size_ms: int
    ) -> None:
        """Log information about segment processing"""
        print(
            f"Processing {len(segments)} segments of {chunk_size_ms / 1000:.1f}s each"
        )

    # ============================================================================
    # AUDIO EXPORT AND FORMAT OPTIMIZATION
    # ============================================================================

    def should_use_m4a_fast_path(
        self, detected_format: str, speed_up_factor: float, file_size_bytes: int
    ) -> bool:
        """Determine if we can use the m4a fast path optimization"""
        # Rough estimate: 1MB ≈ 8 minutes of audio at typical bitrates
        estimated_duration_ms = (file_size_bytes / 1024 / 1024) * 8 * 60 * 1000

        return (
            detected_format == "m4a"
            and speed_up_factor == 1.0
            and estimated_duration_ms <= MAX_CHUNK_DURATION_MS
        )

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
        transcription = await self.transcribe_audio_segment(file_tuple)
        return [transcription]

    @time_it
    def export_audio_to_optimal_format(
        self, segment: AudioSegment, buffer: io.BytesIO, detected_audio_format: str
    ) -> tuple[str, str]:
        """Export audio to optimal format for transcription and return format info"""

        def determine_optimal_export_format(detected_audio_format: str) -> str:
            """Choose optimal export format based on detected audio format"""
            format_optimization_map = {
                "m4a": "ogg",  # Keep as-is (best)
                "mp4": "ogg",  # Convert to m4a
                "mp3": "mp4",  # Convert to m4a
                "wav": "ogg",  # Convert to m4a
                "flac": "ogg",  # Convert to m4a
                "ogg": "ogg",  # Keep as-is
                "webm": "ogg",  # Convert to m4a
            }
            return format_optimization_map.get(detected_audio_format, "ogg")

        def determine_optimal_bitrate(
            detected_audio_format: str, duration_minutes: float
        ) -> str:
            """Choose optimal bitrate based on detected format and duration"""
            if detected_audio_format in ["m4a", "mp4"]:
                return "64k"  # AAC is efficient at low bitrates
            elif detected_audio_format == "ogg":
                return "48k"  # Opus is very efficient
            else:
                return "96k"  # Higher for other formats

        optimal_export_format = OPTIMAL_EXPORT_FORMAT
        optimal_bitrate = determine_optimal_bitrate(
            detected_audio_format, len(segment) / 60000
        )

        segment.export(buffer, format=optimal_export_format, bitrate=optimal_bitrate)
        return optimal_export_format, optimal_bitrate

    # ============================================================================
    # TRANSCRIPTION PROCESSING
    # ============================================================================

    async def transcribe_audio_segment(
        self, file_tuple: tuple[str, io.BytesIO, str]
    ) -> TranscriptionVerbose | Transcription:
        """Transcribe audio segment using OpenAI API"""
        return await self.intelligence_client.audio.transcriptions.create(
            file=file_tuple,
            model=WHISPER_MODEL,
        )

    async def process_segment_with_index(
        self, segment: AudioSegment, index: int, detected_audio_format: str
    ) -> tuple[int, TranscriptionVerbose | Transcription]:
        """Process audio segment and return with index for ordering"""

        def create_audio_buffer() -> io.BytesIO:
            """Create a new audio buffer"""
            return io.BytesIO()

        def log_segment_export_info(
            segment_index: int, buffer: io.BytesIO, export_format: str
        ) -> None:
            """Log information about segment export with actual format"""

            def calculate_buffer_size_in_kilobytes(buffer: io.BytesIO) -> float:
                """Calculate buffer size in kilobytes"""
                return buffer.getbuffer().nbytes / 1024

            buffer_size_kb = calculate_buffer_size_in_kilobytes(buffer)
            print(
                f"Segment {segment_index}: Size of exported buffer in {export_format} in kb: {buffer_size_kb}"
            )

        def create_openai_file_tuple(
            buffer: io.BytesIO, export_format: str
        ) -> tuple[str, io.BytesIO, str]:
            """Create file tuple for OpenAI API with actual export format"""
            return (
                f"audio.{export_format}",
                buffer,
                f"audio/{export_format}",
            )

        buffer = create_audio_buffer()
        export_format, bitrate = self.export_audio_to_optimal_format(
            segment, buffer, detected_audio_format
        )
        log_segment_export_info(index, buffer, export_format)
        buffer.seek(0)

        file_tuple = create_openai_file_tuple(buffer, export_format)
        transcription = await self.transcribe_audio_segment(file_tuple)

        return index, transcription

    async def process_audio_segments_concurrently(
        self, segments: list[AudioSegment], detected_audio_format: str
    ) -> list[tuple[int, TranscriptionVerbose | Transcription]]:
        """Process all audio segments concurrently"""
        return await asyncio.gather(
            *[
                self.process_segment_with_index(segment, index, detected_audio_format)
                for index, segment in enumerate(segments)
            ]
        )

    def assemble_final_transcriptions(
        self,
        transcription_segments: list[tuple[int, TranscriptionVerbose | Transcription]],
    ) -> list[TranscriptionVerbose | Transcription]:
        """Assemble final transcription results in correct order"""

        def sort_transcriptions_by_index(
            transcription_segments: list[
                tuple[int, TranscriptionVerbose | Transcription]
            ],
        ) -> list[tuple[int, TranscriptionVerbose | Transcription]]:
            """Sort transcription segments by their original index"""
            return sorted(transcription_segments, key=lambda x: x[0])

        def extract_transcription_results(
            sorted_segments: list[tuple[int, TranscriptionVerbose | Transcription]],
        ) -> list[TranscriptionVerbose | Transcription]:
            """Extract transcription results from sorted segments"""
            return [
                transcription_segment for _, transcription_segment in sorted_segments
            ]

        sorted_segments = sort_transcriptions_by_index(transcription_segments)
        return extract_transcription_results(sorted_segments)

    # ============================================================================
    # MAIN TRANSCRIPTION PIPELINE
    # ============================================================================

    @time_it
    async def transcribe(
        self,
        audio_file: UploadFile,
        chunk_size_ms: int | None = None,
        speed_up_factor: float = 1.0,
    ) -> list[TranscriptionVerbose | Transcription]:
        """Transcribe audio file with functional pipeline"""
        reset_file = self.reset_file_position(audio_file)
        detected_audio_format = self.determine_audio_format(audio_file)
        self.log_file_information(audio_file, detected_audio_format)

        # Fast path optimization for m4a files
        if self.should_use_m4a_fast_path(
            detected_audio_format, speed_up_factor, audio_file.size or 0
        ):
            print("Using m4a fast path - skipping re-encoding")
            return await self.transcribe_m4a_directly(audio_file)

        # Existing pipeline for all other cases
        raw_audio = self.load_audio_with_fallback(reset_file, detected_audio_format)
        processed_audio = self.apply_speed_modification(raw_audio, speed_up_factor)

        optimal_chunk_size = chunk_size_ms or self.calculate_optimal_chunk_duration(
            len(raw_audio)
        )
        audio_segments = self.split_audio_into_segments(
            processed_audio, optimal_chunk_size
        )
        self.log_segment_processing_info(audio_segments, optimal_chunk_size)

        transcription_segments = await self.process_audio_segments_concurrently(
            audio_segments, detected_audio_format
        )
        return self.assemble_final_transcriptions(transcription_segments)
