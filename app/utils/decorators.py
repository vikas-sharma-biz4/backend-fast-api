"""
Decorators for cross-cutting concerns.
Demonstrates decorator pattern for logging function execution times.
"""
import time
import functools
from typing import Callable, TypeVar, ParamSpec
from datetime import datetime

P = ParamSpec("P")
R = TypeVar("R")


def log_execution_time(func: Callable[P, R]) -> Callable[P, R]:
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
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            print(
                f"[{start_datetime}] ⏱️  {func.__module__}.{func.__name__} "
                f"executed in {execution_time:.4f}s"
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(
                f"[{start_datetime}] ❌ {func.__module__}.{func.__name__} "
                f"failed after {execution_time:.4f}s: {str(e)}"
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.time()
        start_datetime = datetime.now().isoformat()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            print(
                f"[{start_datetime}] ⏱️  {func.__module__}.{func.__name__} "
                f"executed in {execution_time:.4f}s"
            )
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            print(
                f"[{start_datetime}] ❌ {func.__module__}.{func.__name__} "
                f"failed after {execution_time:.4f}s: {str(e)}"
            )
            raise
    
    # Check if function is a coroutine function
    if hasattr(func, "__code__"):
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    # Fallback: assume async if we can't determine
    return async_wrapper

