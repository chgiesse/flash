# AUTO GENERATED FILE - DO NOT EDIT

import typing  # noqa: F401
from typing_extensions import TypedDict, NotRequired, Literal  # noqa: F401
from dash.development.base_component import Component, _explicitize_args

ComponentType = typing.Union[
    str,
    int,
    float,
    Component,
    None,
    typing.Sequence[typing.Union[str, int, float, Component, None]],
]

NumberType = typing.Union[
    typing.SupportsFloat, typing.SupportsInt, typing.SupportsComplex
]


class SSE(Component):
    """A SSE component.
    The SSE component makes it possible to collect data from e.g. a ResponseStream. It's a wrapper around the SSE.js library.
    https://github.com/mpetazzoni/sse.js

    Keyword arguments:

    - id (string; optional):
        Unique ID to identify this component in Dash callbacks.

    - concat (boolean; optional):
        A boolean indicating if the stream values should be concatenated.

    - done (boolean; optional):
        A boolean indicating if the (current) stream has ended.

    - options (dict; optional):
        Options passed to the SSE constructor.

        `options` is a dict with keys:

        - headers (dict with strings as keys and values of type string; optional):
            - headers.

        - payload (string; optional):
            - payload as a Blob, ArrayBuffer, Dataview, FormData,
            URLSearchParams, or string.

        - method (string; optional):
            - HTTP Method.

        - withCredentials (boolean; optional):
            - flag, if credentials needed.

        - start (boolean; optional):
            - flag, if streaming should start automatically.

        - debug (boolean; optional):
            - debugging flag.

    - update_component (boolean; optional):
        A boolean indicating if the strea, should update components.

    - url (string; optional):
        URL of the endpoint.

    - value (string; optional):
        The data value. Either the latest, or the concatenated depending
        on the `concat` property."""

    _children_props = []
    _base_nodes = ["children"]
    _namespace = "flash"
    _type = "SSE"
    Options = TypedDict(
        "Options",
        {
            "headers": NotRequired[typing.Dict[typing.Union[str, float, int], str]],
            "payload": NotRequired[typing.Union[str]],
            "method": NotRequired[str],
            "withCredentials": NotRequired[bool],
            "start": NotRequired[bool],
            "debug": NotRequired[bool],
        },
    )

    def __init__(
        self,
        id: typing.Optional[typing.Union[str, dict]] = None,
        options: typing.Optional["Options"] = None,
        url: typing.Optional[str] = None,
        concat: typing.Optional[bool] = None,
        value: typing.Optional[str] = None,
        done: typing.Optional[bool] = None,
        update_component: typing.Optional[bool] = None,
        **kwargs
    ):
        self._prop_names = [
            "id",
            "concat",
            "done",
            "options",
            "update_component",
            "url",
            "value",
        ]
        self._valid_wildcard_attributes = []
        self.available_properties = [
            "id",
            "concat",
            "done",
            "options",
            "update_component",
            "url",
            "value",
        ]
        self.available_wildcard_properties = []
        _explicit_args = kwargs.pop("_explicit_args")
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(SSE, self).__init__(**args)


setattr(SSE, "__init__", _explicitize_args(SSE.__init__))
