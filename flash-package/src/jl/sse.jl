# AUTO GENERATED FILE - DO NOT EDIT

export sse

"""
    sse(;kwargs...)

A SSE component.
The SSE component makes it possible to collect data from e.g. a ResponseStream. It's a wrapper around the SSE.js library.
https://github.com/mpetazzoni/sse.js
Keyword arguments:
- `id` (String; optional): Unique ID to identify this component in Dash callbacks.
- `concat` (Bool; optional): A boolean indicating if the stream values should be concatenated.
- `done` (Bool; optional): A boolean indicating if the (current) stream has ended.
- `options` (optional): Options passed to the SSE constructor.. options has the following type: lists containing elements 'headers', 'payload', 'method', 'withCredentials', 'start', 'debug'.
Those elements have the following types:
  - `headers` (Dict with Strings as keys and values of type String; optional): - headers
  - `payload` (String; optional): - payload as a Blob, ArrayBuffer, Dataview, FormData, URLSearchParams, or string
  - `method` (String; optional): - HTTP Method
  - `withCredentials` (Bool; optional): - flag, if credentials needed
  - `start` (Bool; optional): - flag, if streaming should start automatically
  - `debug` (Bool; optional): - debugging flag
- `update_component` (Bool; optional): A boolean indicating if the strea, should update components.
- `url` (String; optional): URL of the endpoint.
- `value` (String; optional): The data value. Either the latest, or the concatenated depending on the `concat` property.
"""
function sse(; kwargs...)
        available_props = Symbol[:id, :concat, :done, :options, :update_component, :url, :value]
        wild_props = Symbol[]
        return Component("sse", "SSE", "flash", available_props, wild_props; kwargs...)
end

