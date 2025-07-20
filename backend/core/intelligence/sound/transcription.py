import io

from openai import AsyncOpenAI
from openai.types.audio import Transcription, TranscriptionVerbose
from pydub import AudioSegment  # type: ignore

from .constants import WHISPER_MODEL


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
        audio_exporter,
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
