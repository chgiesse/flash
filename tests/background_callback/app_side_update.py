import asyncio
from dash import Dash, Input, Output, html, callback

from tests.background_callback.utils import get_background_callback_manager

background_callback_manager = get_background_callback_manager()
handle = background_callback_manager.handle

app = Dash(__name__, background_callback_manager=background_callback_manager)

app.layout = html.Div(
    [
        html.Button(id="run-button", children="Run"),
        html.Button(id="cancel-button", children="Cancel"),
        html.Div(id="status", children="Finished"),
        html.Div(id="result", children="No results"),
        html.Div(id="side-status"),
    ]
)
app.test_lock = lock = background_callback_manager.test_lock


@callback(
    Output("result", "children"),
    [Input("run-button", "n_clicks")],
    background=True,
    progress=Output("status", "children"),
    progress_default="Finished",
    cancel=[Input("cancel-button", "n_clicks")],
    interval=0,
    prevent_initial_call=True,
)
async def update_output(set_progress, n_clicks):
    for i in range(4):
        set_progress(f"Progress {i}/4")
        await asyncio.sleep(1)
    return f"Clicked '{n_clicks}'"


@callback(
    Output("side-status", "children"),
    [Input("status", "children")],
    prevent_initial_call=True,
)
def update_side(progress):
    return f"Side {progress}"


if __name__ == "__main__":
    from quart import Quart

    server = Quart(__name__)
    app.init_server(server)
    server.run(debug=True)
