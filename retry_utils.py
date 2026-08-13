import asyncio
import random
import functools

from logging_setup import get_logger

logger = get_logger("retry")


def async_retry(max_retries: int = 3, base_backoff: float = 2, retry_exceptions=(Exception,)):
    """Decorator for async functions. Retries with exponential backoff + jitter
    on any exception in `retry_exceptions`, then re-raises after the last attempt."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exc = e
                    wait = base_backoff ** attempt + random.uniform(0, 1)
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_retries}): {e}. "
                        f"Retrying in {wait:.1f}s"
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(wait)
            logger.error(f"{func.__name__} failed after {max_retries} attempts: {last_exc}")
            raise last_exc

        return wrapper

    return decorator
