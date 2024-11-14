from multiprocessing import Value
from dash.exceptions import PreventUpdate
from werkzeug.exceptions import HTTPException
import numpy as np
import functools
import quart
import operator
import json
import dash
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

import pytest
import dash
from dash import Dash, Input, State, dcc, html, Output
from dash.dash import _ID_LOCATION
from dash.exceptions import NoLayoutException

def get_routing_inputs_app():
    app = Dash(
        __name__,
        use_pages=True,
        routing_callback_inputs={
            "hash": State(_ID_LOCATION, "hash"),
            "language": Input("language", "value"),
        },
    )
    # Page with layout from a variable: should render and not be impacted
    # by routing callback inputs
    dash.register_page(
        "home",
        layout=html.Div("Home", id="contents"),
        path="/",
    )

    # Page with a layout function, should see the routing callback inputs
    # as keyword arguments
    def layout1(hash: str = None, language: str = "en", **kwargs):
        translations = {
            "en": "Hash says: {}",
            "fr": "Le hash dit: {}",
        }
        return html.Div(translations[language].format(hash), id="contents")

    dash.register_page(
        "function_layout",
        path="/function-layout",
        layout=layout1,
    )
    app.layout = html.Div(
        [
            dcc.Dropdown(id="language", options=["en", "fr"], value="en"),
            dash.page_container,
        ]
    )
    return app

app = get_routing_inputs_app()


if __name__ == "__main__":
    app.run(
        debug=True,
    ) 