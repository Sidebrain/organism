from pathlib import Path

from fastapi import UploadFile

from .constants import SUPPORTED_AUDIO_FORMATS


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
