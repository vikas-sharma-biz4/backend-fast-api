"""
Decorators for cross-cutting concerns.
Demonstrates decorator pattern for logging function execution times.
"""
import time
import functools
import logging
from typing import Callable, TypeVar, ParamSpec, Coroutine, Any, Union, overload, cast
from datetime import datetime

P = ParamSpec("P")
R = TypeVar("R")

logger = logging.getLogger(__name__)


@overload
def log_execution_time(
    func: Callable[P, Coroutine[Any, Any, R]]
) -> Callable[P, Coroutine[Any, Any, R]]: ...


@overload
def log_execution_time(func: Callable[P, R]) -> Callable[P, R]: ...


def log_execution_time(
    func: Callable[P, R] | Callable[P, Coroutine[Any, Any, R]]
) -> Callable[P, R] | Callable[P, Coroutine[Any, Any, R]]:
    """
    Decorator that logs function execution time.
    Works with both sync and async functions.

    Example:
        @log_execution_time
        async def my_async_function():
            await asyncio.sleep(1)
    """
    @functools.wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.time()
        start_datetime = datetime.now().isoformat()

        try:
            # Type ignore: We know func is a coroutine function here
            result = await func(*args, **kwargs)  # type: ignore[misc]
            execution_time = time.time() - start_time

            logger.info(
                f"[{start_datetime}] ⏱️  {func.__module__}.{func.__name__} "
                f"executed in {execution_time:.4f}s"
            )

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"[{start_datetime}] ❌ {func.__module__}.{func.__name__} "
                f"failed after {execution_time:.4f}s: {str(e)}",
                exc_info=True
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.time()
        start_datetime = datetime.now().isoformat()

        try:
            # Type ignore: func is checked to be sync, so result is R
            result = func(*args, **kwargs)  # type: ignore[call-overload]
            execution_time = time.time() - start_time

            logger.info(
                f"[{start_datetime}] ⏱️  {func.__module__}.{func.__name__} "
                f"executed in {execution_time:.4f}s"
            )

            # Cast to R since we know func is sync
            return cast(R, result)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"[{start_datetime}] ❌ {func.__module__}.{func.__name__} "
                f"failed after {execution_time:.4f}s: {str(e)}",
                exc_info=True
            )
            raise

    # Check if function is a coroutine function
    if hasattr(func, "__code__"):
        import inspect
        if inspect.iscoroutinefunction(func):
            # Type ignore: async_wrapper is a coroutine function that returns R when awaited
            return async_wrapper  # type: ignore[return-value]
        else:
            return sync_wrapper  # type: ignore[return-value]

    # Fallback: assume async if we can't determine
    return async_wrapper  # type: ignore[return-value]
