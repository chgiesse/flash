from __future__ import annotations

from contextvars import copy_context
from typing import TYPE_CHECKING, Any, Callable, Dict
import asyncio
import pkgutil
import sys
import mimetypes
import time
import inspect
import flask

from dash.fingerprint import check_fingerprint
from dash import _validate
from dash.exceptions import PreventUpdate, InvalidResourceError
from .base_server import BaseDashServer, RequestAdapter

if TYPE_CHECKING:  # pragma: no cover - typing only
    from dash import Dash


class FlaskDashServer(BaseDashServer):

    def __init__(self, server: flask.Flask) -> None:
        self.server: flask.Flask = server
        self.server_type = "flask"
        super().__init__()

    def __call__(self, *args: Any, **kwargs: Any):
        # Always WSGI
        return self.server(*args, **kwargs)

    @staticmethod
    def create_app(name: str = "__main__", config: Dict[str, Any] | None = None):
        app = flask.Flask(name)
        if config:
            app.config.update(config)
        return app

    def register_assets_blueprint(
        self, blueprint_name: str, assets_url_path: str, assets_folder: str
    ):
        bp = flask.Blueprint(
            blueprint_name,
            __name__,
            static_folder=assets_folder,
            static_url_path=assets_url_path,
        )
        self.server.register_blueprint(bp)

    def register_error_handlers(self):
        @self.server.errorhandler(PreventUpdate)
        def _handle_error(_):
            return "", 204

        @self.server.errorhandler(InvalidResourceError)
        def _invalid_resources_handler(err):
            return err.args[0], 404

    def register_prune_error_handler(self, secret: str, get_traceback_func: Callable[[str, BaseException], str]):
        @self.server.errorhandler(Exception)
        def _wrap_errors(error):
            tb = get_traceback_func(secret, error)
            return tb, 500

    def add_url_rule(
        self,
        rule: str,
        view_func: Callable[..., Any],
        endpoint: str | None = None,
        methods: list[str] | None = None,
    ):
        self.server.add_url_rule(
            rule, view_func=view_func, endpoint=endpoint, methods=methods or ["GET"]
        )

    def before_request(self, func: Callable[[], Any]):
        # Flask expects a callable; user responsibility not to pass None
        self.server.before_request(func)

    def after_request(self, func: Callable[[Any], Any]):
        # Flask after_request expects a function(response) -> response
        self.server.after_request(func)

    def run(self, host: str, port: int, debug: bool, **kwargs: Any):
        self.server.run(host=host, port=port, debug=debug, **kwargs)

    def make_response(
        self,
        data: str | bytes | bytearray,
        mimetype: str | None = None,
        content_type: str | None = None,
    ):
        return flask.Response(data, mimetype=mimetype, content_type=content_type)

    def jsonify(self, obj: Any):
        return flask.jsonify(obj)

    def setup_catchall(self, dash_app: Dash):
        def catchall(*args, **kwargs):
            return dash_app.index(*args, **kwargs)

        # pylint: disable=protected-access
        dash_app._add_url("<path:path>", catchall, methods=["GET"])

    def setup_index(self, dash_app: Dash):
        def index(*args, **kwargs):
            return dash_app.index(*args, **kwargs)

        # pylint: disable=protected-access
        dash_app._add_url("", index, methods=["GET"])

    def serve_component_suites(
        self, dash_app: Dash, package_name: str, fingerprinted_path: str
    ):
        path_in_pkg, has_fingerprint = check_fingerprint(fingerprinted_path)
        _validate.validate_js_path(dash_app.registered_paths, package_name, path_in_pkg)
        extension = "." + path_in_pkg.split(".")[-1]
        mimetype = mimetypes.types_map.get(extension, "application/octet-stream")
        package = sys.modules[package_name]
        dash_app.logger.debug(
            "serving -- package: %s[%s] resource: %s => location: %s",
            package_name,
            package.__version__,
            path_in_pkg,
            package.__path__,
        )
        data = pkgutil.get_data(package_name, path_in_pkg)
        response = flask.Response(data, mimetype=mimetype)
        if has_fingerprint:
            response.cache_control.max_age = 31536000  # 1 year
        else:
            response.add_etag()
            tag = response.get_etag()[0]
            request_etag = flask.request.headers.get("If-None-Match")
            if f'"{tag}"' == request_etag:
                response = flask.Response(None, status=304)
        return response

    def setup_component_suites(self, dash_app: Dash):
        def serve(package_name, fingerprinted_path):
            return self.serve_component_suites(
                dash_app, package_name, fingerprinted_path
            )

        # pylint: disable=protected-access
        dash_app._add_url(
            "_dash-component-suites/<string:package_name>/<path:fingerprinted_path>",
            serve,
        )

    # pylint: disable=unused-argument
    def dispatch(self, dash_app: Dash):
        def _dispatch():
            body = flask.request.get_json()
            # pylint: disable=protected-access
            g = dash_app._initialize_context(body)
            func = dash_app._prepare_callback(g, body)
            args = dash_app._inputs_to_vals(g.inputs_list + g.states_list)
            ctx = copy_context()
            partial_func = dash_app._execute_callback(func, args, g.outputs_list, g)
            response_data = ctx.run(partial_func)
            if asyncio.iscoroutine(response_data):
                raise Exception(
                    "You are trying to use a coroutine without dash[async]. "
                    "Please install the dependencies via `pip install dash[async]` and ensure "
                    "that `use_async=False` is not being passed to the app."
                )
            g.dash_response.set_data(response_data)
            return g.dash_response

        async def _dispatch_async():
            body = flask.request.get_json()
            # pylint: disable=protected-access
            g = dash_app._initialize_context(body)
            func = dash_app._prepare_callback(g, body)
            args = dash_app._inputs_to_vals(g.inputs_list + g.states_list)
            ctx = copy_context()
            partial_func = dash_app._execute_callback(func, args, g.outputs_list, g)
            response_data = ctx.run(partial_func)
            if asyncio.iscoroutine(response_data):
                response_data = await response_data
            g.dash_response.set_data(response_data)
            return g.dash_response

        if getattr(dash_app, "_use_async", False):
            return _dispatch_async
        return _dispatch

    def _serve_default_favicon(self):

        return flask.Response(
            pkgutil.get_data("dash", "favicon.ico"), content_type="image/x-icon"
        )

    def register_timing_hooks(self, _first_run: bool):
        # Define timing hooks inside method scope and register them
        def _before_request() -> None:
            flask.g.timing_information = {  # type: ignore[attr-defined]
                "__dash_server": {"dur": time.time(), "desc": None}
            }

        def _after_request(response: flask.Response):  # type: ignore[name-defined]
            timing_information = flask.g.get("timing_information", None)  # type: ignore[attr-defined]
            if timing_information is None:
                return response
            dash_total = timing_information.get("__dash_server", None)
            if dash_total is not None:
                dash_total["dur"] = round((time.time() - dash_total["dur"]) * 1000)
            for name, info in timing_information.items():
                value = name
                if info.get("desc") is not None:
                    value += f';desc="{info["desc"]}"'
                if info.get("dur") is not None:
                    value += f";dur={info['dur']}"
                response.headers.add("Server-Timing", value)
            return response

        self.before_request(_before_request)
        self.after_request(_after_request)

    def register_callback_api_routes(self, callback_api_paths: Dict[str, Callable[..., Any]]):
        """
        Register callback API endpoints on the Flask app.
        Each key in callback_api_paths is a route, each value is a handler (sync or async).
        The view function parses the JSON body and passes it to the handler.
        """
        for path, handler in callback_api_paths.items():
            endpoint = f"dash_callback_api_{path}"
            route = path if path.startswith("/") else f"/{path}"
            methods = ["POST"]

            if inspect.iscoroutinefunction(handler):

                async def _async_view_func(*args, handler=handler, **kwargs):
                    data = flask.request.get_json()
                    result = await handler(**data) if data else await handler()
                    return flask.jsonify(result)

                view_func = _async_view_func
            else:

                def _sync_view_func(*args, handler=handler, **kwargs):
                    data = flask.request.get_json()
                    result = handler(**data) if data else handler()
                    return flask.jsonify(result)

                view_func = _sync_view_func

            # Flask 2.x+ supports async views natively
            self.server.add_url_rule(
                route, endpoint=endpoint, view_func=view_func, methods=methods
            )


class FlaskRequestAdapter(RequestAdapter):
    """Flask implementation using property-based accessors."""

    def __init__(self, server: flask.Flask) -> None:
        self.server_type = "flask"
        self.server: flask.Flask = server
        super().__init__()

    def __call__(self, *args: Any, **kwds: Any):
        return self

    @property
    def args(self):
        return flask.request.args

    @property
    def root(self):
        return flask.request.url_root

    def get_json(self):  # kept as method
        return flask.request.get_json()

    @property
    def is_json(self):
        return flask.request.is_json

    @property
    def cookies(self):
        return flask.request.cookies

    @property
    def headers(self):
        return flask.request.headers

    @property
    def url(self):
        return flask.request.url

    @property
    def full_path(self):
        return flask.request.full_path

    @property
    def remote_addr(self):
        return flask.request.remote_addr

    @property
    def origin(self):
        return getattr(flask.request, "origin", None)

    @property
    def path(self):
        return flask.request.path
