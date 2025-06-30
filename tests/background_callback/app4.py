import asyncio
from dash import Dash, Input, Output, State, dcc, html

from tests.background_callback.utils import get_background_callback_manager

bg_callback_manager = get_background_callback_manager()
handle = bg_callback_manager.handle


app = Dash(__name__, background_callback_manager=bg_callback_manager)
app.layout = html.Div(
    [
        dcc.Input(id="input", value="hello, world"),
        html.Button(id="run-button", children="Run"),
        html.Button(id="cancel-button", children="Cancel"),
        html.Div(id="status", children="Finished"),
        html.Div(id="result", children="No results"),
    ]
)


@app.callback(
    Output("result", "children"),
    [Input("run-button", "n_clicks"), State("input", "value")],
    progress=Output("status", "children"),
    progress_default="Finished",
    cancel=[Input("cancel-button", "n_clicks")],
    interval=500,
    prevent_initial_call=True,
    background=True,
)
async def update_output(set_progress, n_clicks, value):
    for i in range(4):
        set_progress(f"Progress {i}/4")
        await asyncio.sleep(1)
    return f"Processed '{value}'"


if __name__ == "__main__":
    from quart import Quart

    server = Quart(__name__)
    app.init_server(server)
    server.run(debug=True)
