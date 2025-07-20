import io
import os

from fastapi import UploadFile
from pydub import AudioSegment  # type: ignore

from .constants import MAX_CHUNK_DURATION_MS, OPTIMAL_EXPORT_FORMAT


# something
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
