from fastapi import UploadFile
from openai import AsyncOpenAI
from openai.types.audio import TranscriptionVerbose


class AudioSense:
    def __init__(self, intelligence_client: AsyncOpenAI) -> None:
        self.intelligence_client = intelligence_client

    async def transcribe(self, audio_file: UploadFile) -> TranscriptionVerbose:
        audio_file.file.seek(0)
        # audio = AudioSegment.from_file(audio_file.file)
        # buffer = io.BytesIO()
        # audio.export(buffer, format="ipod")
        # buffer.seek(0)
        file_tuple = (audio_file.filename, audio_file.file, audio_file.content_type)

        try:
            transcription = await self.intelligence_client.audio.transcriptions.create(
                file=file_tuple,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
            return transcription
        except Exception as e:
            raise e
