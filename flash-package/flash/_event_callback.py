from ._hooks import hooks
from ._utils import recursive_to_plotly_json
from ._callback import clientside_callback
from .SSE import SSE
from dataclasses import dataclass
from dash import html, State, Input, Output, MATCH
from dash.dependencies import DashDependency
from dash.dcc import Store
import typing as _t
import json
import inspect
import hashlib


SSE_CALLBACK_ENDPOINT: _t.Final[str] = "/dash_update_component_sse"
STEAM_SEPERATOR: _t.Final[str] = "__concatsep__"
SSE_CALLBACK_ID_KEY: _t.Final[str] = "sse_callback_id"

ERROR_TOKEN: _t.Final = "[ERROR]"
INIT_TOKEN: _t.Final = "[INIT]"
DONE_TOKEN: _t.Final = "[DONE]"
RUNNING_TOKEN: _t.Final = "[RUNNING]"

signal_type = _t.Literal["[ERROR]", "[INIT]", "[DONE]", "[RUNNING]"]


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
                SSE(id=self.ids.sse(callback_id), concat=concat),
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
    reset_props: _t.Dict

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
    reset_props: _t.Dict = {},
) -> str:
    """Generate a clientside callback function to reset SSE connection based on close_on conditions."""

    # Generate component IDs
    store_id = SSECallbackComponent.ids.store(callback_id)
    store_id_obj = json.dumps(store_id)

    sse_id = SSECallbackComponent.ids.sse(callback_id)
    sse_id_obj = json.dumps(sse_id)

    # Create the close_on conditions check
    close_conditions = []
    for i, (dependency, desired_state) in enumerate(close_on):
        if isinstance(desired_state, str):
            condition = f'value{i} === "{desired_state}"'
        elif isinstance(desired_state, bool):
            condition = f"value{i} === {str(desired_state).lower()}"
        elif isinstance(desired_state, (int, float)):
            condition = f"value{i} === {desired_state}"
        elif desired_state is None:
            condition = f"value{i} === null"
        else:
            condition = f"value{i} === {json.dumps(desired_state)}"
        close_conditions.append(condition)

    # Create the reset_props assignments
    reset_props_assignments = []
    for component_id, props in reset_props.items():
        if isinstance(props, dict):
            props_str = json.dumps(props)
            reset_props_assignments.append(f'setProps("{component_id}", {props_str});')
        else:
            reset_props_assignments.append(
                f'setProps("{component_id}", {{value: {json.dumps(props)}}});'
            )

    reset_props_code = "\n                ".join(reset_props_assignments)

    # Create the function parameters
    param_names = [f"value{i}" for i in range(len(close_on[:-1]))]
    args_str = ", ".join(param_names)

    # Create the condition check
    condition_check = " && ".join(close_conditions)
    js_code = f"""
        function({args_str}, sseUrl) {{
            if ( !sseUrl ) {{
                return window.dash_clientside.no_update;
            }}

            if (!{condition_check}) {{
                return window.dash_clientside.no_update;
            }}

            setProps = window.dash_clientside.set_props;
            setProps({sse_id_obj}, {{done: true, url: null}});
            setProps({store_id_obj}, {{data: {{}}}});

            {reset_props_code}
        }}
    """

    return js_code


def generate_clientside_callback(input_ids, sse_callback_id, prevent_initial_call):
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
                    url: "{SSE_CALLBACK_ENDPOINT}",
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


def stream_props(component_id: str | _t.Dict, props: _t.Dict):
    """Generate notification props for the specified component ID."""
    response = [RUNNING_TOKEN, component_id, recursive_to_plotly_json(props)]
    event = ServerSentEvent(json.dumps(response) + STEAM_SEPERATOR)
    return event.encode()


def event_callback(
    *dependencies,
    on_error: _t.Optional[_t.Callable] = None,
    cancel: _t.Optional[_t.List[_t.Tuple[DashDependency, _t.Any]]] = None,
    reset_props: _t.Dict = {},
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
        _SSEServerObjects.add_func(sse_obj, callback_id)

        clientside_function = generate_clientside_callback(
            param_names, callback_id, prevent_initial_call
        )
        clientside_callback(
            clientside_function,
            *dependencies,
            prevent_initial_call=prevent_initial_call,
        )

        @hooks.layout()
        def add_sse_component(layout):
            component = SSECallbackComponent(callback_id, concat)
            return (
                [component] + layout
                if isinstance(layout, list)
                else [component, layout]
            )

        if cancel:
            sse_state = (
                State(SSECallbackComponent.ids.sse(callback_id), "url"),
                SSE_CALLBACK_ENDPOINT,
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

        return func

    return decorator


clientside_callback(
    f"""
    function(message, processedData, sseId) {{
        if (!message) {{ return processedData || 0; }}

        const TOKENS = {{
            DONE: "{DONE_TOKEN}",
            INIT: "{INIT_TOKEN}",
            RUNNING: "{RUNNING_TOKEN}",
            ERROR: "{ERROR_TOKEN}"
        }};

        const setProps = window.dash_clientside.set_props;
        const messageList = message.split("{STEAM_SEPERATOR}");
        let startIdx = processedData || 0;

        if (messageList[messageList.length - 1] === '') {{
            messageList.pop();
        }}

        const newMessages = messageList.slice(startIdx);

        newMessages.forEach(messageStr => {{
            try {{
                const [status, componentId, props] = JSON.parse(messageStr);

                switch (status) {{
                    case TOKENS.INIT:
                        processedData = 1;
                        setProps(sseId, {{done: false}});
                        break;

                    case TOKENS.DONE:
                        processedData = 0;
                        setProps(sseId, {{done: true, url: null}});
                        break;

                    case TOKENS.ERROR: {{
                        processedData = 0;
                        const resetProps = props.reset_props || {{}};
                        if (props.handle_error) {{
                            window.alert("Error occurred while processing stream - " + props.error);
                        }}
                        for (const [rcid, rprops] of Object.entries(resetProps)) {{
                            setProps(rcid, rprops);
                        }}
                        setProps(sseId, {{done: true, url: null}});
                        break;
                    }}

                    case TOKENS.RUNNING:
                        setProps(componentId, props);
                        processedData++;
                }}
            }} catch (e) {{
                processedData = 0;
                setProps(sseId, {{done: true, url: null}});
            }}
        }});

        return processedData;
    }}
    """,
    Output(SSECallbackComponent.ids.store(MATCH), "data"),
    Input(SSECallbackComponent.ids.sse(MATCH), "value"),
    State(SSECallbackComponent.ids.store(MATCH), "data"),
    State(SSECallbackComponent.ids.sse(MATCH), "id"),
    prevent_initial_call=True,
)
