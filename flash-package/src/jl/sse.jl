# AUTO GENERATED FILE - DO NOT EDIT

export sse

"""
    sse(;kwargs...)

A SSE component.
The SSE component makes it possible to collect data from e.g. a ResponseStream. It's a wrapper around the SSE.js library.
https://github.com/mpetazzoni/sse.js
Keyword arguments:
- `id` (String; optional): Unique ID to identify this component in Dash callbacks.
- `animate_chunk` (Real; optional): Chunk size (i.e. number of characters) for the animation.
- `animate_delay` (Real; optional): If set, each character is delayed by some amount of time. Used to animate the stream.
- `animate_prefix` (String; optional): Prefix to be excluded from the animation.
- `animate_suffix` (String; optional): Suffix to be excluded from the animation.
- `animation` (String; optional): The animation of the data.
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
- `url` (String; optional): URL of the endpoint.
- `value` (String; optional): The data value. Either the latest, or the concatenated depending on the `concat` property.
"""
function sse(; kwargs...)
        available_props = Symbol[:id, :animate_chunk, :animate_delay, :animate_prefix, :animate_suffix, :animation, :concat, :done, :options, :url, :value]
        wild_props = Symbol[]
        return Component("sse", "SSE", "flash", available_props, wild_props; kwargs...)
end

