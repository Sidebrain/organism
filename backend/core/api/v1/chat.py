import time
from typing import AsyncGenerator

from fastapi import APIRouter
from openai import AsyncOpenAI
from sse_starlette.sse import EventSourceResponse

from core.config import OPENAI_API_KEY
from core.sockets.types import Choice, ChoiceDelta, StreamingResponse

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)


@router.get("/stream", deprecated=True)
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

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    response = StreamingResponse(
                        id=chunk.id,
                        created=chunk.created,
                        model=chunk.model,
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
                id=chunk.id,
                created=chunk.created,
                model=chunk.model,
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
