import functools

from anyio import fail_after


def timeout_after(timeout: int = 10):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with fail_after(timeout):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
