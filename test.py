import asyncio
import random
import dash_mantine_components as dmc
import dash
import time
from dash import (
    Dash,
    Input, 
    Output, 
    _dash_renderer, 
    callback,   
    Patch, 
    clientside_callback, 
    no_update,
    ALL,
    MATCH,
    ctx, 
    set_props
)

from random import choice


_dash_renderer._set_react_version("18.2.0")

external_scripts = ["https://unpkg.com/dash.nprogress@latest/dist/dash.nprogress.js"]

app = Dash(__name__) # 
server = app.server
print(app.server.name)
create_test_btn_id = lambda index: {"index": index, "type": "test-btn"}

def create_appshell(content):
    return dmc.MantineProvider(
        forceColorScheme='dark',
        children=dmc.AppShell(
            [
                dmc.AppShellHeader("", px=25),
                dmc.AppShellNavbar(dmc.Stack(
                    [
                        dmc.NavLink(href='/page-1', label='Page 1'),
                        dmc.NavLink(href='/page-2', label='Page 2'),
                        dmc.NavLink(href='/page-3', label='Page 3'),
                    ]
                )),
                dmc.AppShellMain(children=content),
            ],
            header={"height": 70},
            padding="xl",    
            navbar={
                "width": 300,
                "breakpoint": "sm",
                "collapsed": {"mobile": True},
            }
        )
    )



app.layout = create_appshell(
    dmc.SimpleGrid(
        cols=2,
        children=[
            # WebSocket(id='graph-data-ws', url='/random_data'),
            dmc.Group([
                dmc.Button('test patch', id='test-btn-1'),
                dmc.Button('test async clientside', id='test-btn-2'),
                dmc.Button('test set props', id='test-btn-3'),  
                dmc.Button('test sync callback', id='test-btn-4'),  
            ]),
            dmc.Group([
                dmc.Button('test pattern matching', id=create_test_btn_id(1)),
                dmc.Button('test pattern matching', id=create_test_btn_id(2)),
                dmc.Button('test pattern matching', id=create_test_btn_id(3)),  
            ]),  
            dmc.Stack([
                dmc.Flex(id='output-1'),
                dmc.Flex(id='output-2'),
                dmc.Flex(id='output-3'),
                dmc.Flex(id='output-4'),
                dmc.Flex(id='output-5'),
                # dcc.Graph(
                #     id='test-graph',
                #     figure=px.scatter()
                # )
            ])
        ]
    )
)


@callback(
    Output('output-1', 'children'),
    Input('test-btn-1', 'n_clicks')
)

async def test1(n_clicks):
    patch = Patch()
    patch.append(n_clicks)
    return patch


clientside_callback(
    '''
    async function(n_clicks) {
        return n_clicks
    }
    ''',
    Output('output-2', 'children'),
    Input('test-btn-2', 'n_clicks')
)   


@callback(
    Output('output-3', 'children'),
    Input('test-btn-3', 'n_clicks'),
    prevent_initial_call=True
)

async def test3(n_clicks):

    timeout = 5

    await set_props(
        'output-3', 
        {
            'children': n_clicks
        }
    )

    await asyncio.sleep(timeout)

    return no_update


@callback(
    Output('output-4', 'children'),
    Input('test-btn-4', 'n_clicks'),
    prevent_initial_call=True
)

def test3(n_clicks):
    time.sleep(2)
    return n_clicks


@callback(
    Output('output-5', 'children'),
    Input({'type': 'test-btn', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)

async def test_all(n_clicks):
    return str(ctx.triggered_id)


@callback(
    Output('output-5', 'children', allow_duplicate=True),
    Input(create_test_btn_id(1), 'n_clicks'),
    prevent_initial_call=True
)

async def test_dup_output(n_clicks):

    return str(ctx.triggered_id)


@callback(
    Output('output-5', 'children', allow_duplicate=True),
    Input(create_test_btn_id(2), 'n_clicks'),
    prevent_initial_call=True
)

async def test_dup_output(n_clicks):
    return str(ctx.triggered_id)


@callback(
    Output({'type': 'test-btn', 'index': MATCH}, 'color'),
    Input({'type': 'test-btn', 'index': MATCH}, 'n_clicks'),
    prevent_initial_call=True
)

async def change_color(n_clicks):
    
    colors = ['red', 'blue', 'lime', 'yellow', 'gray', 'pink']
    color = choice(colors)
    return color

if __name__ == '__main__':
    app.run(
        debug=True, 
        dev_tools_ui=True,
        dev_tools_silence_routes_logging=True,
        port=8050
    )   