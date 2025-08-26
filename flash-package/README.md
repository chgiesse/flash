<p align="center">
    <img src="flash-logo.png" alt="logo" width=300 >
</p>
<p align="center">
    <img src="https://badgen.net/pypi/license/dash-flash">
    <a href="https://pypi.org/project/dash-flash/">
    <img src="https://badgen.net/pypi/v/dash-flash">
    </a>
    <img src="https://static.pepy.tech/personalized-badge/dash-flash?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads">
</p>

Flash is an async‑first, drop‑in replacement for Dash. It swaps Flask for Quart (ASGI) under the hood so your Dash apps can run true async callbacks, speak Server‑Sent Events (SSE), and use websockets without workarounds. On top of the Dash API you know, Flash adds streaming superpowers designed to work together:

- event_callback — fire on server-side events and long‑running tasks
- stream_props (used inside event_callback) — yield progressive UI updates directly into component props via native SSE

Build reactive dashboards that don’t just update—they stream.

## Table of contents

- [Getting started](#getting-started)
- [Basic callbacks](#basic-callbacks)
- [Event callback](#event-callback)
    - [Stream Props](#stream-props)
    - [Basic Stream](#basic-event-callback)
    - [Endless Stream](#endless-event-callback)
    - [Cancel streams](#cancel-streams)
    - [Handle error](#handle-error)
    - [Reset props](#reset-props)

## Why use Flash?

- Async everywhere: Write `async def` callbacks and endpoints; await databases, APIs, and background work naturally.
- Progressive rendering: Push partial results as they’re ready using `event_callback` + `stream_props` (native SSE, no polling).
- Real‑time UX: Out‑of‑the‑box SSE and websockets for live metrics, logs, and notifications.
- Familiar by design: Keep Dash’s component model, layout patterns, and callback signatures—just add async and streaming when you need it.

## How is it different from Dash?

- Runtime: `Quart` (ASGI) instead of `Flask` (WSGI) to enable native async I/O.
- Callbacks: Supports `async def` callbacks and async endpoints without threads or hacks.
- Streaming: New `event_callback` decorator and `stream_props` helper provide native SSE streams for progressive prop updates
- Realtime transports: SSE and websockets are first‑class citizens.
- Compatibility: Most Dash apps run as‑is. For streaming use cases, switch to `event_callback` or add `stream_props` to target props; deploy with an ASGI server.


## Getting started

#### Install

```
pip install dash-flash
```

#### Basic app

```python
from flash import Flash, Input, Output, callback, html

app = Flash(__name__)

btn = html.Button("click me", id="button")
content = html.Div(id="output")

app.layout = html.Div([btn, content])

@callback(
    Output(content, "children"),
    Input(btn, "n_clicks")
)
async def update(clicked):
    return "Hello World"
```

## Basic Callbacks
Async callbacks don’t inherently speed up your application, but they enable **efficient** concurrency for `I/O-bound workloads`.
If a callback performs heavy or blocking work, keep it synchronous—such tasks are executed in a dedicated thread.
A typical use case is aggregating responses from multiple HTTP endpoints or running parallel database queries.
```python
from .data import get_data_1, get_data_2, get_data_3
from .figures import create_figures

from flash import Input, Output, callback
import asyncio

@callback(
    Ouput("figure-container", "children"),
    Input("input", "value"),
)
async def update(value):
    data = await asyncio.gather(
        get_data_1(value),
        get_data_2(value),
        get_data_3(value)
    )

    updated_figure = create_figures(data)
    return updated_figures
```

## Event Callback
Server-Sent Events (SSEs) are a server push technology that keeps an HTTP connection open, allowing servers to continuously stream updates to clients. They are typically used for sending messages, data streams, or real-time updates directly to the browser via the native JavaScript EventSource API.

fvent callbacks build on this principle by using async generator functions that yield updates instead of returning once. This enables:

* Progressive UI updates (e.g., streaming partial results).
* Endless streams (e.g., real-time dashboards, stock tickers, monitoring).

The API mirrors Dash’s callback design, but with two key differences:

1. No explicit output needed – updates are applied with stream_props.
2. `stream_props` behaves like set_props, needs to be yield.

### Stream Props
The stream_props function allows you to send UI updates on the fly and follows the set_props API by Dash, while enhancing it with batch updates which reduces network overhead and quicker UI updates. The function can be used as follows:

```python
# Single updates
yield stream_props(component_id="cid", props={"children": "Hello Stream"})
yield stream_props("cid", {"children": "Hello Stream"})
# Batch updates
yield stream_props(batch=[
    ("cid", {"children": "Hello Stream"}),
    ("btn", {"disablesd": True}),
])
yield stream_props([
    ("cid", {"children": "Hello Stream"}),
    ("btn", {"disablesd": True}),
])
```

### Basic Event Callback

This example (from Dash’s background callback docs) shows how a background callback is no longer necessary—eliminating the need for extra services like Celery + Redis.

```python
# data.py
import pandas as pd
import asyncio

async def get_data(chunk_size: int):
    df: pd.DataFrame = data.gapminder()
    total_rows = df.shape[0]

    while total_rows > 0:
        await asyncio.sleep(2)
        end = len(df) - total_rows + chunk_size
        total_rows -= chunk_size
        update_data = df[:end].to_dict("records")
        df.drop(df.index[:end], inplace=True)
        yield update_data, df.columns
```

A more realistic use case would be streaming query results with *SQLAlchemy async*:

```python
# data.py
from sqlalchemy.ext.asyncio import AsyncConnection

async def get_data(connection: AsyncConnection):
    result = await connection.stream(select(users_table))

    async for partition in result.partitions(100):
        print("list of rows: %s" % partition)
        return partition

```
Hooking it into your app with `event_callback`:
```python
#app.py
from flash import Input, event_callback, stream_props

@event_callback(Input("start-stream-button", "n_clicks"))
async def update_table(_):

    yield stream_props([
        ("start-stream-button", {"loading": True}),
        ("cancel-stream-button", {"display": "flex"})
    ])

    progress = 0
    chunk_size = 500
    async for data_chunk, colnames in get_data(chunk_size):
        if progress == 0:
            columnDefs = [{"field": col} for col in colnames]
            update = {"rowData": data_chunk, "columnDefs": columnDefs}
        else:
            update = {"rowTransaction": {"add": data_chunk}}

        yield stream_props("dash-ag-grid", update)

        if len(data_chunk) == chunk_size:
            yield NotificationsContainer.send_notification(
                title="Starting stream!",
                message="Notifications in Dash, Awesome!",
                color="lime",
            )

        progress += 1

    yield stream_props("start-stream-button", {"loading": False, "children": "Reload"})
    yield stream_props("reset-strea-button", {"display": "none"})
```

### Endless Event Callback
Event callbacks are lightweight and stateless, making them ideal for continuous real-time streams:

```python
from .data import get_latest_stock_data
from flash import Input, event_callback, stream_props

@callback(Input("start-stream-button", "n_clicks"))
async def stream_stock_data(_):
    while True:
        x, s1, s2 = await get_latest_stock_data()
        update = [dict(x=[[x], [x]], y=[[s1], [s2]]), [0, 1], 100]

    yield stream_props("stock-graph", {"extendData": update})
```

## Cancel streams

- Configure `cancel=[(Input("id", "value"), desired_state), ...]` on `@event_callback` to close the active SSE stream when a condition is *NOT* met. Lets consider a layout with three tabs and the stream runs in tab *dashboard* and you want that the stream only runs when that tab is open, you can set `(Input("tabs", "value"), "dashboard")`
- Proper canceling prevents stale EventSource connections from pushing late updates, reduces network chatter, and avoids extra rendering work in the browser.
- On cancel, marks the SSE as done and applies any `reset_props` so the UI returns to a clean, predictable state.
- Common triggers: reset/cancel buttons, page or tab changes, or beginning a new run that invalidates the previous stream.

```python
@event_callback(
    ...,
    cancel=[
        (Input("tabs", "value"), "dashboard"),
        (Input("c-btn", "n_clicks"), 0)
    ]
)
```

## Handle error

- `on_error` is a callable that receives the raised error (e.g., `def on_error(e): ...`). Use it to emit a final user-facing message and perform cleanup when the stream fails.
- Typical cleanup: unsubscribe from a stream topic, close file/DB handles, revoke a background task token, or write telemetry.
- Flash also emits an SSE error signal so the client can coordinate default error UI and cleanup. Combine with `reset_props` to leave the interface in a known-good state.

## Reset props

- Configure `reset_props=[(component_id, {prop: value, ...}), ...]` on `@event_callback` to restore the UI after cancel or error.
- Use it to re-enable start buttons, hide cancel controls, clear progress text/spinners, and restore placeholders.
- These updates are applied automatically when a stream is canceled or errors, alongside closing the SSE connection and clearing transient state.
