import time
from typing import AsyncGenerator

from fastapi import APIRouter
from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sse_starlette.sse import EventSourceResponse

from core.config import OPENAI_API_KEY

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


class ChatRequest(BaseModel):
    # conversation_id: str
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
async def chat_stream_words(message: str) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            # Create streaming completion with OpenAI
            stream = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": message}],
                stream=True,
                temperature=0.7,
                max_tokens=1000,
            )

            completion_id = f"chatcmpl-{int(time.time())}"
            created_time = int(time.time())

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response = StreamingResponse(
                        id=completion_id,
                        created=created_time,
                        model="gpt-4",
                        choices=[
                            Choice(
                                index=0,
                                delta=ChoiceDelta(
                                    content=chunk.choices[0].delta.content
                                ),
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
                created=created_time,
                model="gpt-4",
                choices=[
                    Choice(index=0, delta=ChoiceDelta(content=""), finish_reason="stop")
                ],
            )

            yield {
                "data": final_response.model_dump_json(by_alias=True),
            }

        except Exception as e:
            # Handle errors gracefully
            error_response = StreamingResponse(
                id=f"chatcmpl-{int(time.time())}",
                created=int(time.time()),
                model="gpt-4",
                choices=[
                    Choice(
                        index=0,
                        delta=ChoiceDelta(content=f"Error: {str(e)}"),
                        finish_reason="error",
                    )
                ],
            )

            yield {
                "data": error_response.model_dump_json(by_alias=True),
            }

    return EventSourceResponse(event_generator())
