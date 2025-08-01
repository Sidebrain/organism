import socketio  # type: ignore[import-untyped]
from openai import AsyncOpenAI

from core.config import OPENAI_API_KEY

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="asgi",
    # logger=True,
    # engineio_logger=True,
)
active_connections: dict[str, dict] = {}


def register_sio_handlers() -> None:
    from . import chat  # noqa: F401
