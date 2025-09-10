from ._hooks import hooks
from ._utils import recursive_to_plotly_json
from ._callback import clientside_callback
from .SSE import SSE
from dataclasses import dataclass
from dash import html, State
from dash.dependencies import DashDependency
from dash.dcc import Store
from dash._get_paths import get_relative_path
import typing as _t
import json
import inspect
import hashlib


SSE_CALLBACK_ENDPOINT: _t.Final[str] = "/dash_update_component_sse"
STEAM_SEPERATOR: _t.Final[str] = "__concatsep__"
SSE_CALLBACK_ID_KEY: _t.Final[str] = "sse_callback_id"

ERROR_TOKEN: _t.Final = "[ERROR]"
SINGLE_UPDATE_TOKEN: _t.Final = "[SINGLE]"
BATCH_UPDATE_TOKEN: _t.Final = "[BATCH]"

signal_type: _t.TypeAlias = _t.Literal["[ERROR]", "[SINGLE]", "[BATCH]"]
batch_props_type: _t.TypeAlias = _t.List[
    _t.Tuple[str | _t.Dict[str, _t.Any], _t.Dict[str, _t.Any]]
]


def get_callback_id(callback_id: str):
    try:
        callback_id_dict = json.loads(callback_id)
        return callback_id_dict["index"]
    except Exception:
        return callback_id


class SSECallbackComponent(html.Div):
    class ids:
        sse = lambda idx: {"type": "dash-event-stream", "index": idx}
        store = lambda idx: {"type": "dash-event-stream-store", "index": idx}

    def __init__(self, callback_id: str, concat: bool = True):
        super().__init__(
            [
                SSE(id=self.ids.sse(callback_id), concat=concat, update_component=True),
                Store(id=self.ids.store(callback_id), data={}, storage_type="memory"),
            ],
        )


@dataclass
class ServerSentEvent:
    data: str
    event: str | None = None
    id: int | None = None
    retry: int | None = None

    def encode(self) -> bytes:
        message = f"data: {self.data}"
        if self.event is not None:
            message = f"{message}\nevent: {self.event}"
        if self.id is not None:
            message = f"{message}\nid: {self.id}"
        if self.retry is not None:
            message = f"{message}\nretry: {self.retry}"
        message = f"{message}\n\n"
        return message.encode("utf-8")


@dataclass
class _SSEServerObject:
    func: _t.Callable
    on_error: _t.Optional[_t.Callable]
    reset_props: batch_props_type

    @property
    def func_name(self):
        return self.func.__name__


class _SSEServerObjects:
    funcs: _t.Dict[str, _SSEServerObject] = {}

    @classmethod
    def add_func(cls, sse_obj: _SSEServerObject, callback_id: str):
        if callback_id in cls.funcs:
            raise KeyError(
                f"callback_id: {callback_id} with name: {sse_obj.func_name} is already registered"
            )

        cls.funcs[callback_id] = sse_obj

    @classmethod
    def get_func(cls, callback_id: str):
        return cls.funcs.get(callback_id)


def generate_reset_callback_function(
    callback_id: str,
    close_on: _t.List[_t.Tuple[DashDependency, _t.Any]],
    reset_props: batch_props_type,
) -> str:
    """Generate a clientside callback function to reset SSE connection based on close_on conditions."""

    # Generate component IDs
    store_id = SSECallbackComponent.ids.store(callback_id)
    store_id_obj = json.dumps(store_id)

    sse_id = SSECallbackComponent.ids.sse(callback_id)
    sse_id_obj = json.dumps(sse_id)

    # Create the close_on conditions check
    # Note: the last dependency in `close_on` is the SSE url, which is passed as `sseUrl` param
    close_conditions = []
    last_index = len(close_on) - 1
    for i, (_dependency, desired_state) in enumerate(close_on):
        var_name = "sseUrl" if i == last_index else f"value{i}"
        if isinstance(desired_state, str):
            condition = f"{var_name} !== {json.dumps(desired_state)}"
        elif isinstance(desired_state, bool):
            condition = f"{var_name} !== {str(desired_state).lower()}"
        elif isinstance(desired_state, (int, float)):
            condition = f"{var_name} !== {desired_state}"
        elif desired_state is None:
            condition = f"{var_name} !== null"
        else:
            condition = f"{var_name} !== {json.dumps(desired_state)}"
        close_conditions.append(condition)

    # Create the reset_props assignments
    reset_props_assignments = []
    for component_id, props in reset_props:
        comp_id_str = json.dumps(component_id)
        if isinstance(props, dict):
            props_str = json.dumps(props)
            reset_props_assignments.append(f"setProps({comp_id_str}, {props_str});")
        else:
            reset_props_assignments.append(
                f"setProps({comp_id_str}, {{value: {json.dumps(props)}}});"
            )

    reset_props_code = "\n                ".join(reset_props_assignments)

    # Create the function parameters
    param_names = [f"value{i}" for i in range(max(len(close_on) - 1, 0))]
    args_str = ", ".join(param_names)
    # Build function parameters list, ensuring valid JS when there are no non-SSE args
    params_list = f"{args_str}, sseUrl" if args_str else "sseUrl"

    # Create the condition check
    condition_check = " && ".join(close_conditions)

    js_code = f"""
        function({params_list}) {{
            if ( !sseUrl ) {{
                return window.dash_clientside.no_update;
            }}

            if ({condition_check}) {{
                return window.dash_clientside.no_update;
            }}

            setProps = window.dash_clientside.set_props;
            setProps({sse_id_obj}, {{done: true, url: null}});
            setProps({store_id_obj}, {{data: {{}}}});

            {reset_props_code}
        }}
    """

    return js_code


def generate_clientside_callback(input_ids, sse_callback_id, prevent_initial_call, sse_url):
    args_str = ", ".join(input_ids)
    start = "false" if prevent_initial_call else "true"
    sse_id_obj = SSECallbackComponent.ids.sse(sse_callback_id)
    str_sse_id = json.dumps(sse_id_obj)
    property_assignments = [f"    'sse_callback_id': '{str_sse_id}'"]

    for input_id in input_ids:
        property_assignments.append(f'    "{input_id}": {input_id}')

    payload_obj = "{\n" + ",\n".join(property_assignments) + "\n}"

    js_code = f"""
        function({args_str}) {{
            // Create payload object with all inputs
            const payload = {{
                ...{payload_obj},
                callback_context: window.dash_clientside.callback_context
            }};

            // Prepare SSE options with the payload
            const sse_options = {{
                payload: JSON.stringify({{ content: payload }}),
                headers: {{ "Content-Type": "application/json" }},
                method: "POST",

            }};

            // Set props for the SSE component
            window.dash_clientside.set_props(
                {str_sse_id},
                {{
                    options: sse_options,
                    url: "{sse_url}",
                }}
            );
        }}
    """

    return js_code


def generate_deterministic_id(func: _t.Callable, dependencies: _t.Tuple) -> str:
    """Should align more with dashs callback id generation."""
    func_identity = f"{func.__module__}.{func.__qualname__}"
    dependency_reprs = sorted([repr(d) for d in dependencies])
    dependencies_string = ";".join(dependency_reprs)
    unique_string = f"{func_identity}|{dependencies_string}"
    return hashlib.sha256(unique_string.encode("utf-8")).hexdigest()


@_t.overload
def stream_props(
    component_id: str | dict[str, _t.Any], props: dict[str, _t.Any], /
) -> bytes:
    ...


@_t.overload
def stream_props(
    batch: list[tuple[str | dict[str, _t.Any], dict[str, _t.Any]]], /
) -> bytes:
    ...


@_t.overload
def stream_props(
    *, batch: list[tuple[str | dict[str, _t.Any], dict[str, _t.Any]]]
) -> bytes:
    ...


def stream_props(
    arg1: str
    | dict[str, _t.Any]
    | list[tuple[str | dict[str, _t.Any], dict[str, _t.Any]]]
    | None = None,
    props: dict[str, _t.Any] | None = None,
    /,
    *,
    batch: list[tuple[str | dict[str, _t.Any], dict[str, _t.Any]]] | None = None,
) -> bytes:
    """
    Create an SSE message to update one or many components.

    Forms:
    >>> stream_props("my-id", {"value": 42})
    >>> stream_props([("id1", {"a": 1}), ("id2", {"b": 2})])
    >>> stream_props(batch=[("id1", {"a": 1}), ("id2", {"b": 2})])
    """

    if batch is not None:
        response = [
            BATCH_UPDATE_TOKEN,
            None,
            [(cid, recursive_to_plotly_json(p)) for cid, p in batch],
        ]

    elif props is None:
        if not isinstance(arg1, list):
            raise TypeError(
                "Batch form requires a list of (component_id, props) tuples."
            )

        response = [
            BATCH_UPDATE_TOKEN,
            None,
            [(cid, recursive_to_plotly_json(p)) for cid, p in arg1],
        ]

    else:
        if arg1 is None or isinstance(arg1, list):
            raise TypeError("Single form requires component_id and props.")

        component_id = arg1
        response = [
            SINGLE_UPDATE_TOKEN,
            component_id,
            recursive_to_plotly_json(props),
        ]

    event = ServerSentEvent(json.dumps(response))
    return event.encode()


def event_callback(
    *dependencies,
    on_error: _t.Optional[_t.Callable] = None,
    cancel: _t.Optional[_t.List[_t.Tuple[DashDependency, _t.Any]]] = None,
    reset_props: batch_props_type = [],
    prevent_initial_call=True,
    concat: bool = True,
):
    def decorator(func: _t.Callable) -> _t.Callable:
        if not inspect.isasyncgenfunction(func):
            raise ValueError("Event callback must be a generator function")

        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        callback_id = generate_deterministic_id(func, dependencies)

        sse_obj = _SSEServerObject(func, on_error, reset_props)
        sse_url = get_relative_path(SSE_CALLBACK_ENDPOINT)
        _SSEServerObjects.add_func(sse_obj, callback_id)

        clientside_function = generate_clientside_callback(
            param_names, callback_id, prevent_initial_call, sse_url
        )
        clientside_callback(
            clientside_function,
            *dependencies,
            prevent_initial_call=prevent_initial_call,
        )

        if cancel:
            sse_state = (
                State(SSECallbackComponent.ids.sse(callback_id), "url"),
                sse_url,
            )
            cancel_w_sse = cancel + [sse_state]
            reset_callback_function = generate_reset_callback_function(
                callback_id, cancel_w_sse, reset_props
            )
            if reset_callback_function:
                reset_dependencies = [dependency for dependency, _ in cancel_w_sse]
                clientside_callback(
                    reset_callback_function,
                    *reset_dependencies,
                    prevent_initial_call=True,
                )


        @hooks.layout()
        def add_sse_component(layout):
            component = SSECallbackComponent(callback_id, concat)
            return (
                [component] + layout
                if isinstance(layout, list)
                else [component, layout]
            )


        return func

    return decorator
