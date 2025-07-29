import asyncio
import time

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


class ChoiceDelta(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    content: str | None = None
    role: str | None = None


class Choice(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    index: int
    delta: ChoiceDelta
    finish_reason: str | None = None


class StreamingResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[Choice]


@router.get("/stream")
async def chat_stream_words() -> EventSourceResponse:
    async def event_generator():
        sentence = "Testing out streaming, by streaming these words brother. Add some more words to the sentence."
        words = sentence.split()
        completion_id = f"chatcmpl-{int(time.time())}"

        for idx, word in enumerate(words):
            await asyncio.sleep(0.3)

            response = StreamingResponse(
                id=completion_id,
                created=int(time.time()),
                model="gpt-4",
                choices=[
                    Choice(
                        index=0,
                        delta=ChoiceDelta(content=word + " "),
                        finish_reason=None,
                    )
                ],
            )

            yield {
                "data": response.model_dump_json(by_alias=True),
            }

        # Final message with finish_reason
        final_response = StreamingResponse(
            id=completion_id,
            created=int(time.time()),
            model="gpt-4",
            choices=[
                Choice(index=0, delta=ChoiceDelta(content=""), finish_reason="stop")
            ],
        )

        yield {
            "data": final_response.model_dump_json(by_alias=True),
        }

    return EventSourceResponse(event_generator())
