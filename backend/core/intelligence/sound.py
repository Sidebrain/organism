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


class AudioFormatDetector:
    """Handles audio format detection from various sources"""

    def __init__(self) -> None:
        self.supported_formats = SUPPORTED_AUDIO_FORMATS

    def determine_audio_format(self, audio_file: UploadFile) -> str:
        """Determine audio format from filename or content-type with fallback"""
        format_from_filename = self._extract_audio_format_from_filename(audio_file)
        if format_from_filename:
            return format_from_filename

        format_from_content_type = self._extract_audio_format_from_content_type(
            audio_file
        )
        if format_from_content_type:
            return format_from_content_type

        return "mp3"  # Default fallback

    def _extract_audio_format_from_filename(self, audio_file: UploadFile) -> str | None:
        """Extract audio format from filename extension. Example: .mp3 -> mp3"""
        if not audio_file.filename:
            return None
        suffix = Path(audio_file.filename).suffix.lower()
        if suffix in self.supported_formats:
            return suffix[1:]  # Remove the dot
        return None

    def _extract_audio_format_from_content_type(
        self, audio_file: UploadFile
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


class AudioFileHandler:
    """Handles file operations and logging for audio files"""

    def reset_file_position(self, audio_file: UploadFile) -> UploadFile:
        """Reset file position to beginning"""
        audio_file.file.seek(0)
        return audio_file

    def log_file_information(self, audio_file: UploadFile, file_format: str) -> None:
        """Log file information for debugging"""
        file_size_kb = self._calculate_file_size_in_kilobytes(audio_file)
        print(f"Size of audio file in {file_format} in kb: {file_size_kb}")

    def _calculate_file_size_in_kilobytes(self, audio_file: UploadFile) -> float:
        """Calculate file size in kilobytes"""
        return (audio_file.size or 0) / 1024


class AudioLoader:
    """Handles audio loading with fallback mechanisms"""

    def load_audio_with_fallback(
        self, audio_file: UploadFile, file_format: str
    ) -> AudioSegment:
        """Load audio with fallback to temporary file if direct loading fails"""
        try:
            return self._load_audio_from_file_object(audio_file, file_format)
        except Exception:
            temp_filename = self._create_temporary_audio_file(audio_file, file_format)
            audio = self._load_audio_from_temporary_file(temp_filename)
            self._cleanup_temporary_file(temp_filename)
            return audio

    def _load_audio_from_file_object(
        self, audio_file: UploadFile, file_format: str
    ) -> AudioSegment:
        """Load audio directly from file object"""
        return AudioSegment.from_file(audio_file.file, format=file_format)

    def _create_temporary_audio_file(
        self, audio_file: UploadFile, file_format: str
    ) -> str:
        """Create temporary file for audio loading fallback"""
        temp_filename = f"temp.{file_format}"
        with open(temp_filename, "wb") as f:
            f.write(audio_file.file.read())
        return temp_filename

    def _load_audio_from_temporary_file(self, temp_filename: str) -> AudioSegment:
        """Load audio from temporary file"""
        return AudioSegment.from_file(temp_filename)

    def _cleanup_temporary_file(self, temp_filename: str) -> None:
        """Remove temporary file"""
        os.unlink(temp_filename)


class AudioSegmenter:
    """Handles audio segmentation and chunking logic"""

    def __init__(self) -> None:
        self.max_chunk_duration_ms = MAX_CHUNK_DURATION_MS

    def calculate_optimal_chunk_duration(self, audio_duration_ms: int) -> int:
        """Calculate optimal chunk duration based on audio length and OpenAI limits"""
        if audio_duration_ms <= self.max_chunk_duration_ms:
            return audio_duration_ms
        return self.max_chunk_duration_ms

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


class AudioExporter:
    """Handles audio export and format optimization"""

    def __init__(self) -> None:
        self.optimal_export_format = OPTIMAL_EXPORT_FORMAT
        self.max_chunk_duration_ms = MAX_CHUNK_DURATION_MS

    def should_use_m4a_fast_path(
        self, detected_format: str, speed_up_factor: float, file_size_bytes: int
    ) -> bool:
        """Determine if we can use the m4a fast path optimization"""
        # Rough estimate: 1MB ≈ 8 minutes of audio at typical bitrates
        estimated_duration_ms = (file_size_bytes / 1024 / 1024) * 8 * 60 * 1000

        return (
            detected_format == "m4a"
            and speed_up_factor == 1.0
            and estimated_duration_ms <= self.max_chunk_duration_ms
        )

    @time_it
    def export_audio_to_optimal_format(
        self, segment: AudioSegment, buffer: io.BytesIO, detected_audio_format: str
    ) -> tuple[str, str]:
        """Export audio to optimal format for transcription and return format info"""
        optimal_export_format = self._determine_optimal_export_format(
            detected_audio_format
        )
        optimal_bitrate = self._determine_optimal_bitrate(
            detected_audio_format, len(segment) / 60000
        )

        segment.export(buffer, format=optimal_export_format, bitrate=optimal_bitrate)
        return optimal_export_format, optimal_bitrate

    def _determine_optimal_export_format(self, detected_audio_format: str) -> str:
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

    def _determine_optimal_bitrate(
        self, detected_audio_format: str, duration_minutes: float
    ) -> str:
        """Choose optimal bitrate based on detected format and duration"""
        if detected_audio_format in ["m4a", "mp4"]:
            return "64k"  # AAC is efficient at low bitrates
        elif detected_audio_format == "ogg":
            return "48k"  # Opus is very efficient
        else:
            return "96k"  # Higher for other formats


class TranscriptionProcessor:
    """Handles transcription processing and API interactions"""

    def __init__(self, intelligence_client: AsyncOpenAI) -> None:
        self.intelligence_client = intelligence_client
        self.whisper_model = WHISPER_MODEL

    async def transcribe_audio_segment(
        self, file_tuple: tuple[str, io.BytesIO, str]
    ) -> TranscriptionVerbose | Transcription:
        """Transcribe audio segment using OpenAI API"""
        return await self.intelligence_client.audio.transcriptions.create(
            file=file_tuple,
            model=self.whisper_model,
        )

    async def process_segment_with_index(
        self,
        segment: AudioSegment,
        index: int,
        detected_audio_format: str,
        audio_exporter: AudioExporter,
    ) -> tuple[int, TranscriptionVerbose | Transcription]:
        """Process audio segment and return with index for ordering"""
        buffer = self._create_audio_buffer()
        export_format, bitrate = audio_exporter.export_audio_to_optimal_format(
            segment, buffer, detected_audio_format
        )
        self._log_segment_export_info(index, buffer, export_format)
        buffer.seek(0)

        file_tuple = self._create_openai_file_tuple(buffer, export_format)
        transcription = await self.transcribe_audio_segment(file_tuple)

        return index, transcription

    def _create_audio_buffer(self) -> io.BytesIO:
        """Create a new audio buffer"""
        return io.BytesIO()

    def _log_segment_export_info(
        self, segment_index: int, buffer: io.BytesIO, export_format: str
    ) -> None:
        """Log information about segment export with actual format"""
        buffer_size_kb = self._calculate_buffer_size_in_kilobytes(buffer)
        print(
            f"Segment {segment_index}: Size of exported buffer in {export_format} in kb: {buffer_size_kb}"
        )

    def _calculate_buffer_size_in_kilobytes(self, buffer: io.BytesIO) -> float:
        """Calculate buffer size in kilobytes"""
        return buffer.getbuffer().nbytes / 1024

    def _create_openai_file_tuple(
        self, buffer: io.BytesIO, export_format: str
    ) -> tuple[str, io.BytesIO, str]:
        """Create file tuple for OpenAI API with actual export format"""
        return (
            f"audio.{export_format}",
            buffer,
            f"audio/{export_format}",
        )


class TranscriptionAssembler:
    """Handles final assembly and ordering of transcription results"""

    def assemble_final_transcriptions(
        self,
        transcription_segments: list[tuple[int, TranscriptionVerbose | Transcription]],
    ) -> list[TranscriptionVerbose | Transcription]:
        """Assemble final transcription results in correct order"""
        sorted_segments = self._sort_transcriptions_by_index(transcription_segments)
        return self._extract_transcription_results(sorted_segments)

    def _sort_transcriptions_by_index(
        self,
        transcription_segments: list[tuple[int, TranscriptionVerbose | Transcription]],
    ) -> list[tuple[int, TranscriptionVerbose | Transcription]]:
        """Sort transcription segments by their original index"""
        return sorted(transcription_segments, key=lambda x: x[0])

    def _extract_transcription_results(
        self, sorted_segments: list[tuple[int, TranscriptionVerbose | Transcription]]
    ) -> list[TranscriptionVerbose | Transcription]:
        """Extract transcription results from sorted segments"""
        return [transcription_segment for _, transcription_segment in sorted_segments]


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
