from functools import wraps
from time import time
from typing import Any, Awaitable, Callable


def time_it(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print(f"Starting {func.__name__}...")
        start = time()
        result = await func(*args, **kwargs)
        end = time()
        print(
            f"Time taken: {end - start} seconds for {func.__name__}, args: {args}, kwargs: {kwargs}"
        )
        return result

    return wrapper
