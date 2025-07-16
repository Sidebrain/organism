from functools import wraps
from time import time
from typing import Awaitable, Callable, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


def time_it(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        print(f"Starting {func.__name__}...")
        start = time()
        result = await func(*args, **kwargs)
        end = time()
        print(
            f"Time taken: {end - start} seconds for {func.__name__}, args: {args}, kwargs: {kwargs}"
        )
        return result

    return wrapper
