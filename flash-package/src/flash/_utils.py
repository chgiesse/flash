import inspect
import warnings
from quart.utils import run_sync


async def _invoke_callback(func, *func_args, **func_kwargs):

    if inspect.iscoroutinefunction(func):
        output_value = await func(*func_args, **func_kwargs)  # %% callback invoked %%

    else:
        output_value = await run_sync(func)(
            *func_args, **func_kwargs
        )  # %% callback invoked %%

        warnings.warn(
            f"Function '{func.__name__}' should be a coroutine function (defined with 'async def'). "
            "While it will still work, this may impact performance and is deprecated.",
            stacklevel=2,
        )

    return output_value
