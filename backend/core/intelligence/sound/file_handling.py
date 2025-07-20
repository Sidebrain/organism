from fastapi import UploadFile


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
