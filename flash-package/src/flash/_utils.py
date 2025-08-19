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


def recursive_to_plotly_json(component):
    """
    Recursively convert a component to a JSON-serializable structure.
    Handles Plotly components, numpy arrays, pandas objects, dates/times, and other special types.

    Parameters:
    -----------
    component: Any
        The component to convert

    Returns:
    --------
    A JSON-serializable representation of the component
    """
    # Base case: simple types don't need conversion
    if component is None or isinstance(component, (str, int, float, bool)):
        return component

    # Try to handle numpy arrays first
    try:
        import numpy as np

        if isinstance(component, np.ndarray):
            return component.tolist()
        elif np.isscalar(component) and not isinstance(
            component, (bool, int, float, complex)
        ):
            return component.item()
    except (ImportError, AttributeError):
        pass

    # Handle pandas objects
    try:
        import pandas as pd

        if isinstance(component, (pd.Series, pd.DataFrame)):
            return component.to_dict()
        elif isinstance(component, pd.Timestamp):
            return component.isoformat()
        elif component is pd.NaT:
            return None
    except (ImportError, AttributeError):
        pass

    # Handle datetime objects
    try:
        import datetime

        if isinstance(component, (datetime.date, datetime.datetime)):
            return component.isoformat()
    except (ImportError, AttributeError):
        pass

    # Handle decimal
    try:
        import decimal

        if isinstance(component, decimal.Decimal):
            return float(component)
    except (ImportError, AttributeError):
        pass

    # Convert component to plotly json if it has the method
    if hasattr(component, "to_plotly_json"):
        component = component.to_plotly_json()

    # Also try other common serialization methods
    if hasattr(component, "tolist"):
        try:
            return component.tolist()
        except Exception:
            pass

    if hasattr(component, "to_dict"):
        try:
            return component.to_dict()
        except Exception:
            pass

    # Make sure component is a dictionary before checking for "props"
    if isinstance(component, dict):
        # Process props
        for key, value in list(component.items()):
            if isinstance(value, list):
                # Process lists of items
                component[key] = [recursive_to_plotly_json(item) for item in value]
            else:
                # Process single items
                component[key] = recursive_to_plotly_json(value)

    # Handle list-type components
    elif isinstance(component, list):
        component = [recursive_to_plotly_json(item) for item in component]

    # As a last resort, try string representation
    else:
        try:
            return str(component)
        except Exception:
            return None

    return component
