import os
from typing import AsyncGenerator

from openai import AsyncOpenAI

from ..config import OPENAI_API_KEY

_async_openai_client: AsyncOpenAI | None = None


async def get_openai_async_client() -> AsyncGenerator[AsyncOpenAI, None]:
    global _async_openai_client
    if _async_openai_client is None:
        _async_openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        yield _async_openai_client
    finally:
        print("client killed")
        pass



