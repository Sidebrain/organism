import asyncio
import time
from typing import AsyncGenerator

import socketio  # type: ignore[import-untyped]

from core.api.v1.chat import Choice, ChoiceDelta, StreamingResponse

sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="asgi",
)


active_connections: dict[str, dict] = {}


@sio.event
async def connect(sid: str, environ: dict) -> None:
    print("connection established")
    print(f"# of active connections: {len(active_connections)}")
    active_connections[sid] = environ


@sio.event
async def hello(sid: str, message: str) -> None:
    print(f"{sid}, {message}")
    await sio.emit(
        "hello",
        "number of active connections: " + str(len(active_connections)),
        to=sid,
    )


@sio.event
async def disconnect(sid: str) -> None:
    print(f"connection closed {sid}")
    del active_connections[sid]


@sio.event
async def request_chat_stream(sid: str, message: str) -> None:
    print(f"request_chat_stream {sid}")
    sentence = (
        "How are you doing on this fine day? Well you see I am a very happy person and I am enjoying my time here."
        + "I am learnign to feel comfortable in boredom, treat myself like a king, and to feel how isolation is impacting me. "
        + "I am learning to be more patient and to be more present in the moment. "
        + "I am learning to be more grateful for the little things in life. "
        + "I am learning to be more present in the moment. "
        + "I am learning to be more grateful for the little things in life. "
    )

    words = sentence.split(" ")

    async def event_generator() -> AsyncGenerator[dict, None]:
        completion_id = f"chatcmpl-{int(time.time())}"
        created_time = int(time.time())

        for word in words:
            response = StreamingResponse(
                id=completion_id,
                created=created_time,
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
            await asyncio.sleep(0.01)

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

    async for chunk in event_generator():
        await sio.emit("chat_stream", chunk, to=sid)
