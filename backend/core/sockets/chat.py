import time

from pydantic import ValidationError

from . import client, sio
from .types import ChatRequest, Choice, ChoiceDelta, StreamingResponse

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
async def request_chat_stream(sid: str, message: dict) -> None:
    print(f"request_chat_stream {sid}")
    try:
        validated_message = ChatRequest.model_validate(message)
    except ValidationError as e:
        print(f"Error: {e}")
        return
    try:
        stream = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": validated_message.message},
            ],
            stream=True,
            temperature=0.7,
            max_tokens=1000,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response = StreamingResponse(
                    id=chunk.id,
                    created=chunk.created,
                    model="gpt-4",
                    choices=[
                        Choice(
                            index=0,
                            delta=ChoiceDelta(content=chunk.choices[0].delta.content),
                            finish_reason=None,
                        )
                    ],
                )

                await sio.emit(
                    "chat_stream",
                    {
                        "data": response.model_dump_json(by_alias=True),
                    },
                    to=sid,
                )
            elif chunk.choices[0].finish_reason is not None:
                # Final message with finish_reason
                final_response = StreamingResponse(
                    id=chunk.id,
                    created=chunk.created,
                    model="gpt-4",
                    choices=[
                        Choice(
                            index=0, delta=ChoiceDelta(content=""), finish_reason="stop"
                        )
                    ],
                )

                await sio.emit(
                    "chat_stream",
                    {
                        "data": final_response.model_dump_json(by_alias=True),
                    },
                    to=sid,
                )
    except Exception as e:
        print(f"Error: {e}")
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
        await sio.emit(
            "chat_stream",
            {
                "data": error_response.model_dump_json(by_alias=True),
            },
            to=sid,
        )
