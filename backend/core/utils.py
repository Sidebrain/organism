import asyncio
from functools import wraps
from time import time
from typing import Awaitable, Callable, ParamSpec, TypeVar, Union, overload

T = TypeVar("T")
P = ParamSpec("P")


@overload
def time_it(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator for synchronous functions"""
    ...


@overload
def time_it(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """Decorator for asynchronous functions"""
    ...


def time_it(  # type: ignore
    func: Union[Callable[P, T], Callable[P, Awaitable[T]]],
) -> Union[Callable[P, T], Callable[P, Awaitable[T]]]:
    """Time execution of both sync and async functions"""

    if asyncio.iscoroutinefunction(func):
        # Handle async functions
        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            print(f"Starting {func.__name__}...")
            start = time()
            result = await func(*args, **kwargs)
            end = time()
            print(
                f"Time taken: {end - start} seconds for {func.__name__}, args: {args}, kwargs: {kwargs}"
            )
            return result

        return async_wrapper
    else:
        # Handle sync functions
        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            print(f"Starting {func.__name__}...")
            start = time()
            result = func(*args, **kwargs)
            end = time()
            print(
                f"Time taken: {end - start} seconds for {func.__name__}, args: {args}, kwargs: {kwargs}"
            )
            return result  # type: ignore

        return sync_wrapper
