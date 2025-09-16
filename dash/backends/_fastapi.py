from contextvars import copy_context, ContextVar
import sys
import mimetypes
import hashlib
import inspect
import pkgutil
import time

from dash.fingerprint import check_fingerprint
from dash import _validate
from dash.exceptions import PreventUpdate, InvalidResourceError
from .base_server import BaseDashServer, RequestAdapter

from fastapi import FastAPI, Request, Response, Body
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response as StarletteResponse
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Scope, Receive, Send
import uvicorn


_current_request_var = ContextVar("dash_current_request", default=None)


def set_current_request(req):
    return _current_request_var.set(req)


def reset_current_request(token):
    _current_request_var.reset(token)


def get_current_request() -> Request:
    req = _current_request_var.get()
    if req is None:
        raise RuntimeError("No active request in context")
    return req


class CurrentRequestMiddleware:
    def __init__(self, app: ASGIApp) -> None:  # type: ignore[name-defined]
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:  # type: ignore[name-defined]
        # non-http/ws scopes pass through (lifespan etc.)
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        token = set_current_request(request)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_current_request(token)


class FastAPIDashServer(BaseDashServer):

    def __init__(self, server: FastAPI):
        self.config = {}
        self.server_type = "fastapi"
        self.server: FastAPI = server
        super().__init__()

    def __call__(self, *args, **kwargs):
        # ASGI: (scope, receive, send)
        if len(args) == 3 and isinstance(args[0], dict) and "type" in args[0]:
            return self.server(*args, **kwargs)
        raise TypeError("FastAPI app must be called with (scope, receive, send)")

    @staticmethod
    def create_app(name="__main__", config=None):
        app = FastAPI()
        app.add_middleware(CurrentRequestMiddleware)

        if config:
            for key, value in config.items():
                setattr(app.state, key, value)
        return app

    def register_assets_blueprint(
        self, blueprint_name, assets_url_path, assets_folder
    ):
        try:
            self.server.mount(
                assets_url_path,
                StaticFiles(directory=assets_folder),
                name=blueprint_name,
            )
        except RuntimeError:
            # directory doesnt exist
            pass

    def register_error_handlers(self):
        @self.server.exception_handler(PreventUpdate)
        async def _handle_error(_request, _exc):
            return Response(status_code=204)

        @self.server.exception_handler(InvalidResourceError)
        async def _invalid_resources_handler(_request, exc):
            return Response(content=exc.args[0], status_code=404)

    def register_prune_error_handler(self, secret, get_traceback_func):
        @self.server.exception_handler(Exception)
        async def _wrap_errors(_error_request, error):
            tb = get_traceback_func(secret, error)
            return PlainTextResponse(tb, status_code=500)

    def _html_response_wrapper(self, view_func):
        async def wrapped(*_args, **_kwargs):
            # If view_func is a function, call it; if it's a string, use it directly
            html = view_func() if callable(view_func) else view_func
            return Response(content=html, media_type="text/html")

        return wrapped

    def setup_index(self, dash_app):
        async def index(request: Request):
            return Response(content=dash_app.index(), media_type="text/html")

        # pylint: disable=protected-access
        dash_app._add_url("", index, methods=["GET"])

    def setup_catchall(self, dash_app):
        @self.server.on_event("startup")
        def _setup_catchall():
            dash_app.enable_dev_tools(
                **self.config, first_run=False
            )  # do this to make sure dev tools are enabled

            async def catchall(request: Request):
                return Response(content=dash_app.index(), media_type="text/html")

            # pylint: disable=protected-access
            dash_app._add_url("{path:path}", catchall, methods=["GET"])

    def add_url_rule(
        self, rule, view_func, endpoint=None, methods=None, include_in_schema=False
    ):
        if rule == "":
            rule = "/"
        if isinstance(view_func, str):
            # Wrap string or sync function to async FastAPI handler
            view_func = self._html_response_wrapper(view_func)
        self.server.add_api_route(
            rule,
            view_func,
            methods=methods or ["GET"],
            name=endpoint,
            include_in_schema=include_in_schema,
        )

    def before_request(self, func):
        # FastAPI does not have before_request, but we can use middleware
        self.server.middleware("http")(self._make_before_middleware(func))

    def after_request(self, func):
        # FastAPI does not have after_request, but we can use middleware
        self.server.middleware("http")(self._make_after_middleware(func))

    def run(self, host, port, debug, **kwargs):
        self.config = dict({"debug": debug} if debug else {}, **kwargs)
        # Uvicorn requires an import string for reload; derive if possible else run without reload.
        if debug:
            caller_frame = inspect.stack()[2]
            module = inspect.getmodule(caller_frame.frame)
            if module and module.__name__ not in ("__main__", None):
                target = f"{module.__name__}:app.server"
                print(f"Running Uvicorn with reload for '{target}'", flush=True)
                uvicorn.run(target, host=host, port=port, reload=True, **kwargs)
                return
        # Fallback: run the FastAPI instance directly (no reload or reload unsupported)
        uvicorn.run(self.server, host=host, port=port, reload=False, **kwargs)

    def make_response(self, data, mimetype=None, content_type=None):
        headers = {}
        if mimetype:
            headers["content-type"] = mimetype
        if content_type:
            headers["content-type"] = content_type
        return Response(content=data, headers=headers)

    def jsonify(self, obj):
        return JSONResponse(content=obj)

    def _make_before_middleware(self, func):
        async def middleware(request, call_next):
            if func is not None:
                if inspect.iscoroutinefunction(func):
                    await func()
                else:
                    func()
            response = await call_next(request)
            return response

        return middleware

    def _make_after_middleware(self, func):
        async def middleware(request, call_next):
            response = await call_next(request)
            if func is not None:
                if inspect.iscoroutinefunction(func):
                    await func()
                else:
                    func()
            return response

        return middleware

    def serve_component_suites(
        self, dash_app, package_name, fingerprinted_path, request
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
        headers = {}
        if has_fingerprint:
            headers["Cache-Control"] = "public, max-age=31536000"
            return StarletteResponse(content=data, media_type=mimetype, headers=headers)
        etag = hashlib.md5(data).hexdigest() if data else ""
        headers["ETag"] = etag
        if request.headers.get("if-none-match") == etag:
            return StarletteResponse(status_code=304)
        return StarletteResponse(content=data, media_type=mimetype, headers=headers)

    def setup_component_suites(self, dash_app):
        async def serve(request: Request, package_name: str, fingerprinted_path: str):
            return self.serve_component_suites(
                dash_app, package_name, fingerprinted_path, request
            )

        # pylint: disable=protected-access
        dash_app._add_url(
            "_dash-component-suites/{package_name}/{fingerprinted_path:path}",
            serve,
        )

    # pylint: disable=unused-argument
    def dispatch(self, dash_app, use_async=False):

        async def _dispatch(request: Request):
            # pylint: disable=protected-access
            body = await request.json()
            g = dash_app._initialize_context(body)  # pylint: disable=protected-access
            func = dash_app._prepare_callback(
                g, body
            )  # pylint: disable=protected-access
            args = dash_app._inputs_to_vals(
                g.inputs_list + g.states_list
            )  # pylint: disable=protected-access
            ctx = copy_context()
            partial_func = dash_app._execute_callback(
                func, args, g.outputs_list, g
            )  # pylint: disable=protected-access
            response_data = ctx.run(partial_func)
            if inspect.iscoroutine(response_data):
                response_data = await response_data
            # Instead of set_data, return a new Response
            return Response(content=response_data, media_type="application/json")

        return _dispatch

    def _serve_default_favicon(self):
        return Response(
            content=pkgutil.get_data("dash", "favicon.ico"), media_type="image/x-icon"
        )

    def register_timing_hooks(self, first_run):
        if not first_run:
            return

        @self.server.middleware("http")
        async def timing_middleware(request: Request, call_next):
            # Before request
            request.state.timing_information = {
                "__dash_server": {"dur": time.time(), "desc": None}
            }
            response = await call_next(request)
            # After request
            timing_information = getattr(request.state, "timing_information", None)
            if timing_information is not None:
                dash_total = timing_information.get("__dash_server", None)
                if dash_total is not None:
                    dash_total["dur"] = round((time.time() - dash_total["dur"]) * 1000)
                headers = MutableHeaders(response.headers)
                for name, info in timing_information.items():
                    value = name
                    if info.get("desc") is not None:
                        value += f';desc="{info["desc"]}"'
                    if info.get("dur") is not None:
                        value += f";dur={info['dur']}"
                    headers.append("Server-Timing", value)
            return response

    def register_callback_api_routes(self, callback_api_paths):
        """
        Register callback API endpoints on the FastAPI app.
        Each key in callback_api_paths is a route, each value is a handler (sync or async).
        Accepts a JSON body (dict) and filters keys based on the handler's signature.
        """
        for path, handler in callback_api_paths.items():
            endpoint = f"dash_callback_api_{path}"
            route = path if path.startswith("/") else f"/{path}"
            methods = ["POST"]
            sig = inspect.signature(handler)
            param_names = list(sig.parameters.keys())

            async def view_func(request: Request, body: dict = Body(...)):
                # Only pass expected params; ignore extras
                kwargs = {
                    k: v for k, v in body.items() if k in param_names and v is not None
                }
                if inspect.iscoroutinefunction(handler):
                    result = await handler(**kwargs)
                else:
                    result = handler(**kwargs)
                return JSONResponse(content=result)

            self.server.add_api_route(
                route,
                view_func,
                methods=methods,
                name=endpoint,
                include_in_schema=True,
            )


class FastAPIRequestAdapter(RequestAdapter):

    def __init__(self):
        self._request: Request = get_current_request()
        super().__init__()

    def __call__(self):
        self._request = get_current_request()
        return self

    @property
    def root(self):
        return str(self._request.base_url)

    @property
    def args(self):
        return self._request.query_params

    @property
    def is_json(self):
        return self._request.headers.get("content-type", "").startswith(
            "application/json"
        )

    @property
    def cookies(self):
        return self._request.cookies

    @property
    def headers(self):
        return self._request.headers

    @property
    def full_path(self):
        return str(self._request.url)

    @property
    def url(self):
        return str(self._request.url)

    @property
    def remote_addr(self):
        client = getattr(self._request, "client", None)
        return getattr(client, "host", None)

    @property
    def origin(self):
        return self._request.headers.get("origin")

    @property
    def path(self):
        return self._request.url.path

    async def get_json(self):  # async method retained
        return await self._request.json()
