import functools
from inspect import iscoroutinefunction

from anyio import get_cancelled_exc_class, move_on_after
from src.config.app_config import app_settings


def check_for_cancellation(func):
    @functools.wraps(func)
    async def wrapper(
        # self,
        *args,
        **kwargs
    ):
        try:
            return await func(
                # self,
                *args,
                **kwargs
            )
        except get_cancelled_exc_class():
            with move_on_after(app_settings.cleanup_timeout) as cleanup_scope:
                cleanup_scope.shield = True
                for arg in args:
                    if hasattr(arg, "close") and iscoroutinefunction(arg.close):
                        await arg.close()
                    elif hasattr(arg, "aclose") and iscoroutinefunction(arg.aclose):
                        await arg.aclose()
                for arg in kwargs.values():
                    if hasattr(arg, "close") and iscoroutinefunction(arg.close):
                        await arg.close()
                    elif hasattr(arg, "aclose") and iscoroutinefunction(arg.aclose):
                        await arg.aclose()
            raise

    return wrapper
