from flask import jsonify
import requests
import pytest

from dash import Dash, Input, Output, html, hooks, set_props


@pytest.fixture
def hook_cleanup():
    yield
    hooks._ns["layout"] = []
    hooks._ns["setup"] = []
    hooks._ns["route"] = []
    hooks._ns["error"] = []
    hooks._ns["callback"] = []
    hooks._ns["index"] = []
    hooks._css_dist = []
    hooks._js_dist = []
    hooks._finals = {}
    hooks._clientside_callbacks = []


def test_hook001_layout(hook_cleanup, dash_duo):
    @hooks.layout()
    async def on_layout(layout):
        return [html.Div("Header", id="header")] + layout

    app = Dash()
    app.layout = [html.Div("Body", id="body")]

    dash_duo.start_server(app)

    dash_duo.wait_for_text_to_equal("#header", "Header")
    dash_duo.wait_for_text_to_equal("#body", "Body")


def test_hook002_setup(hook_cleanup):
    setup_title = None

    @hooks.setup()
    def on_setup(app: Dash):
        nonlocal setup_title
        setup_title = app.title

    app = Dash(title="setup-test")
    app.layout = html.Div("setup")

    assert setup_title == "setup-test"


def test_hook003_route(hook_cleanup, dash_duo):
    @hooks.route(methods=("POST",))
    async def hook_route():
        return jsonify({"success": True})

    app = Dash()
    app.layout = html.Div("hook route")

    dash_duo.start_server(app)
    response = requests.post(f"{dash_duo.server_url}/hook_route")
    data = response.json()
    assert data["success"]


def test_hook004_error(hook_cleanup, dash_duo):
    @hooks.error()
    async def on_error(error):
        set_props("error", {"children": str(error)})

    app = Dash()
    app.layout = [html.Button("start", id="start"), html.Div(id="error")]

    @app.callback(Input("start", "n_clicks"), prevent_initial_call=True)
    async def on_click(_):
        raise Exception("hook error")

    dash_duo.start_server(app)
    dash_duo.wait_for_element("#start").click()
    dash_duo.wait_for_text_to_equal("#error", "hook error")


def test_hook005_callback(hook_cleanup, dash_duo):
    @hooks.callback(
        Output("output", "children"),
        Input("start", "n_clicks"),
        prevent_initial_call=True,
    )
    async def on_hook_cb(n_clicks):
        return f"clicked {n_clicks}"

    app = Dash()
    app.layout = [
        html.Button("start", id="start"),
        html.Div(id="output"),
    ]

    dash_duo.start_server(app)
    dash_duo.wait_for_element("#start").click()
    dash_duo.wait_for_text_to_equal("#output", "clicked 1")


def test_hook006_priority_final(hook_cleanup, dash_duo):
    @hooks.layout(final=True)
    async def hook_final(layout):
        return html.Div([html.Div("final")] + [layout], id="final-wrapper")

    @hooks.layout()
    async def hook1(layout):
        layout.children.append(html.Div("first"))
        return layout

    @hooks.layout()
    async def hook2(layout):
        layout.children.append(html.Div("second"))
        return layout

    @hooks.layout()
    async def hook3(layout):
        layout.children.append(html.Div("third"))
        return layout

    @hooks.layout(priority=6)
    async def hook4(layout):
        layout.children.insert(0, html.Div("Prime"))
        return layout

    app = Dash()

    app.layout = html.Div([html.Div("layout")], id="body")

    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal("#final-wrapper > div:first-child", "final")
    dash_duo.wait_for_text_to_equal("#body > div:first-child", "Prime")
    dash_duo.wait_for_text_to_equal("#body > div:nth-child(2)", "layout")
    dash_duo.wait_for_text_to_equal("#body > div:nth-child(3)", "first")
    dash_duo.wait_for_text_to_equal("#body > div:nth-child(4)", "second")
    dash_duo.wait_for_text_to_equal("#body > div:nth-child(5)", "third")


def test_hook007_hook_index(hook_cleanup, dash_duo):
    @hooks.index()
    async def hook_index(index: str):
        body = "<body>"
        ib = index.find(body) + len(body)
        injected = '<div id="hooked">Hooked</div>'
        new_index = index[ib:] + injected + index[: ib + 1]
        return new_index

    app = Dash()
    app.layout = html.Div(["index"])

    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal("#hooked", "Hooked")


def test_hook008_hook_distributions(hook_cleanup, dash_duo):
    js_uri = "https://example.com/none.js"
    css_uri = "https://example.com/none.css"
    hooks.script([{"external_url": js_uri, "external_only": True}])
    hooks.stylesheet([{"external_url": css_uri, "external_only": True}])

    app = Dash()
    app.layout = html.Div("distribute")

    dash_duo.start_server(app)

    assert dash_duo.find_element(f'script[src="{js_uri}"]')
    assert dash_duo.find_element(f'link[href="{css_uri}"]')


def test_hook009_hook_clientside_callback(hook_cleanup, dash_duo):
    hooks.clientside_callback(
        "(n) => `Called ${n}`",
        Output("hook-output", "children"),
        Input("hook-start", "n_clicks"),
        prevent_initial_call=True,
    )

    app = Dash()
    app.layout = [
        html.Button("start", id="hook-start"),
        html.Div(id="hook-output"),
    ]

    dash_duo.start_server(app)

    dash_duo.wait_for_element("#hook-start").click()
    dash_duo.wait_for_text_to_equal("#hook-output", "Called 1")
