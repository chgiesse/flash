from multiprocessing import Value
from dash.exceptions import PreventUpdate
import numpy as np
import operator
import json
from dash import (
    Dash,
    Input,
    Output,
    State,
    html,
    dcc,
    dash_table,
    no_update,
    callback_context,
    set_props
)

class context:
    calls = 0
    callback_contexts = []

app = Dash(__name__)
app.layout = html.Div(
    [
        html.Div(
            style={"display": "block"},
            children=[
                html.Div(
                    [
                        html.Label("ID: input-number-1"),
                        dcc.Input(id="input-number-1", type="number", value=0),
                    ]
                ),
                html.Div(
                    [
                        html.Label("ID: input-number-2"),
                        dcc.Input(id="input-number-2", type="number", value=0),
                    ]
                ),
                html.Div(
                    [
                        html.Label("ID: sum-number"),
                        dcc.Input(
                            id="sum-number", type="number", value=0, disabled=True
                        ),
                    ]
                ),
            ],
        ),
        html.Div(id="results"),
    ]
)

@app.callback(
    Output("sum-number", "value"),
    [Input("input-number-1", "value"), Input("input-number-2", "value")],
)
async def update_sum_number(n1, n2):
    context.calls = context.calls + 1
    context.callback_contexts.append(callback_context.triggered)

    return n1 + n2

@app.callback(
    Output("results", "children"),
    [
        Input("input-number-1", "value"),
        Input("input-number-2", "value"),
        Input("sum-number", "value"),
    ],
)
async def update_results(n1, n2, nsum):
    context.calls = context.calls + 1
    context.callback_contexts.append(callback_context.triggered)
    print(context.calls, flush=True)
    print(len(context.callback_contexts), flush=True)
    keys0 = list(map(operator.itemgetter("prop_id"), context.callback_contexts[0])) 

    return [
        "{} + {} = {}".format(n1, n2, nsum),
        html.Br(),
        "ctx.triggered={}".format(callback_context.triggered),
    ]


if __name__ == "__main__":
    app.run(debug=True)