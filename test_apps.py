from multiprocessing import Value
from dash.exceptions import PreventUpdate
from werkzeug.exceptions import HTTPException
import numpy as np
import functools
import quart
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
app = Dash(__name__)
app.layout = html.Div([dcc.Input(id="a"), dcc.Input(id="b"), html.P(id="c")])

@app.callback(Output("a", "value"), [Input("b", "value")])
def set_a(b):
    return ((b or "") + "X")[:100]

@app.callback(
    [Output("b", "value"), Output("c", "children")], [Input("a", "value")]
)
def set_bc(a):
    return [a, a]

if __name__ == "__main__":
    app.run(
        debug=True,
        use_debugger=True,
        use_reloader=False,
        dev_tools_hot_reload=False
    ) 