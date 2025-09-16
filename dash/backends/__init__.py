from typing import Literal
import importlib

from .base_server import BaseDashServer, RequestAdapter


_backend_imports = {
    "flask": ("dash.backends._flask", "FlaskDashServer", "FlaskRequestAdapter"),
    "fastapi": ("dash.backends._fastapi", "FastAPIDashServer", "FastAPIRequestAdapter"),
    "quart": ("dash.backends._quart", "QuartDashServer", "QuartRequestAdapter"),
}

request_adapter: RequestAdapter
backend: BaseDashServer


def get_backend(name: Literal["flask", "fastapi", "quart"]):
    module_name, server_class, request_class = _backend_imports[name.lower()]
    try:
        module = importlib.import_module(module_name)
        server = getattr(module, server_class)
        request_adapter = getattr(module, request_class)
        return server, request_adapter
    except KeyError as e:
        raise ValueError(f"Unknown backend: {name}") from e
    except ImportError as e:
        raise ImportError(
            f"Could not import module '{module_name}' for backend '{name}': {e}"
        ) from e
    except AttributeError as e:
        raise AttributeError(
            f"Module '{module_name}' does not have class '{server_class}' for backend '{name}': {e}"
        ) from e


__all__ = [
    "get_backend",
    "request_adapter",
    "backend",
]
