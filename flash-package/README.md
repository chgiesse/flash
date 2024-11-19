# Flash

## *Quart async Patch of Dash*.

`Flash` is a async patch of the [Plotly Dash](https://github.com/plotly/dash) library, building on Quart as backend instead of Flask. It is very inspired by the already existing [dash-async](https://github.com/snehilvj/async-dash) repo, but covering all **features up to `Dash` 2.18.2**

Quarts async capabilities are directly baked into the standard library, making it easy to inject into existing projects. 

Flash makes it possible to run **true async callbacks** and layout functions while running sync functions in a separate thread (_asyncio.run_in_executor_).

With [dash-extensions](https://www.dash-extensions.com/) you can create native websocket components and handle serverside events - making your application realtime compatible. 

## Installation 
```
pip install dash-flash
```

## Table of Contents
- [Motivation](#motivation)
- [A Notice](#a-notice)
- [Known Issues](#known-issues)
- [Usage](#usage)
- [TODO](#todo)

## Motivation
One of the biggest pain points in Dash was handling database requests, which often required:
- Adding multiple callbacks to fetch a "lazy" component
- Rendering the real component only when the lazy component's ID appears
- Creating complex pattern matching callbacks for each component's data

Dash Flash addresses these challenges by:
- Ensuring I/O bound tasks don't block each other
- Better state management via the URL due to async layout functions
- Native websocket and HTTP/2 support 

Future improvements may include: 
- native Websocket component which spawns and manages the websocket itself
- LazyLoad component like [dash-grocery](https://github.com/IcToxi/dash-grocery), this will also increase responsiveness and overall better UI feeling
- shared callbacks / channel callbacks like [dash-devices](https://github.com/richlegrand/dash_devices) offered. Will most likly be implemented with redis PubSub
- ?? new routing system based on blueprints enabling parallel routes ??

## A Notice
- Background callbacks must run synchronously
- For Dash testing, use `dash_duo_mp` instead of `dash_duo`
- currently not tested in prod, will soon on a basic K8s cluster running in a Docker container

### Known Issues
- not all tests pass - detailed look in TEST_LOGS.md 
    - 10 integration tests
    - 2 unit tests

### Usage 

modules that need to be imported from `flash`

```python
from flash import (
    Flash,
    get_app,
    register_page,
    page_registry,
    ctx,
    set_props,
    callback,
    clientse_callback,
    no_update,
    page_container,
)
```

Modules that can be imported from flash but also from dash - seeking your feedback here, would you preffer to keep them separate or just import from flash? 
```python
from flash import (
    Input,  
    Output, 
    State, 
    ClientsideFunction,
    MATCH,
    ALL, 
    ALLSMALLER, 
    get_asset_url,
    get_relative_path,
    strip_relative_path,
)
```

1. Gather async functions in callback:

```python
from flash import Flash, callback, Input, Output, html
from dash import _dash_renderer

import time 
import asyncio


_dash_renderer._set_react_version("18.2.0")

external_scripts = ["https://unpkg.com/dash.nprogress@latest/dist/dash.nprogress.js"]

app = Flash(__name__, external_scripts=external_scripts)


class ids:
    sync_btn_id = "sync-btn-id" 
    async_btn_id = "async-btn-id"
    sync_output = "sync-output"
    async_output = "async-output"


app.layout = html.Div(
    [
        html.Button("Sync", id=ids.sync_btn_id),
        html.Button("Async", id=ids.async_btn_id),
        html.Div(id=ids.sync_output)
        html.Div(id=ids.async_output)
    ]
)


def long_running(sleep):
    time.sleep(sleep)

async def long_running_async(sleep):
    await asyncio.sleep(sleep)


@callback(
    Output(ids.sync_output, "children"),
    Input(ids.sync_btn_id, "n_clicks"),
    prevent_initial_call=True
)

def update_sync(_):
    start_time = time.perf_counter()
    long_running(1)
    long_running(0.7)
    long_running(.5)
    duration = time.perf_counter() - start_time
    return duration


@callback(
    Output(ids.async_output, "children"),
    Input(ids.async_btn_id, "n_clicks"),
    prevent_initial_call=True,
)

async def update_async(_):
    start_time = time.perf_counter()
    await asyncio.gather(
        long_running_async(1),
        long_running_async(0.7),
        long_running_async(.5) 
    )
    duration = time.perf_counter() - start_time
    return duration


if __name__ == "__main__":
    app.run(debug=True)
```

2. websocket support with [dash-extensions](https://github.com/emilhe/dash-extensions) - _(inspired by [dash-async](https://github.com/snehilvj/async-dash))_ 

```python
import asyncio
import random

from flash import Flash, Output, Input
from dash import html, dcc
from dash_extensions import WebSocket
from quart import websocket, json


app = Dash(__name__)


class ids:
    websocket_id = "ws"
    graph_id = "graph"


layout = html.Div([
    WebSocket(id=ids.websocket_id, url="ws://127.0.0.1:8050/test-ws"), 
    dcc.Graph(id=ids.graph_id)
])


clientside_callback(
    """
    function(msg) {
        if (msg) {
            const data = JSON.parse(msg.data);
            return {data: [{y: data, type: "scatter"}]};
        } else {
            return window.dash_clientside.no_update;
        }
    }
    """,
    Output(ids.graph_id, "figure"),
    [Input(ids.websocket_id, "message")],
)


@app.server.websocket("/test-ws")
async def ws():
    while True:
        output = json.dumps([random.randint(200, 1000) for _ in range(6)])
        await websocket.send(output)
        await asyncio.sleep(1)


if __name__ == "__main__":
    app.run(debug=True)
```

## TODO
- add Serverside Event example