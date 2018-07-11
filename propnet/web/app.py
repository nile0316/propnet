import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt

from dash.dependencies import Input, Output, State

from propnet import log_stream
from propnet.web.layouts_models import model_layout, models_index
from propnet.web.layouts_symbols import symbol_layout, symbols_index

from dash_react_graph_vis import GraphComponent
from propnet.web.utils import graph_conversion, parse_path, AESTHETICS
from propnet.core.graph import Graph

from propnet.ext.matproj import MPRester
from pydash import set_, get

from flask_caching import Cache

# TODO: Fix math rendering

app = dash.Dash()
server = app.server
app.config.supress_callback_exceptions = True  # TODO: remove this?
app.scripts.config.serve_locally = True
app.title = "Property Network Project"
route = dcc.Location(id='url', refresh=False)

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem', 'CACHE_DIR': '.tmp'
})

mpr = MPRester()

g = Graph().graph

# Define default graph component
@app.callback(Output('graph_explorer', 'children'),
              [Input('graph_options', 'values')])
def get_graph_component(props):
    aesthetics = AESTHETICS.copy()
    show_properties = 'show_properties' in props
    show_models = 'show_models' in props
    print(props)
    print("Updating graph to {}, {}".format(show_properties, show_models))
    set_(aesthetics, "node_aesthetics.Symbol.show_labels", show_properties)
    set_(aesthetics, "node_aesthetics.Model.show_labels", show_models)
    graph_data = graph_conversion(g, aesthetics=aesthetics)
    print(graph_data)
    from uuid import uuid4
    graph_component = html.Div(
        id=str(uuid4()),
        children=[GraphComponent(id=str(uuid4()), graph=graph_data,
                                 options=AESTHETICS['global_options'])],
        style={'width': '100%', 'height': '800px'})
    return [graph_component]


# Do I really need to redo this code?
graph_data = graph_conversion(g)
graph_component = html.Div(
    id='graph_component',
    children=[GraphComponent(id='propnet-graph', graph=graph_data,
                             options=AESTHETICS['global_options'])],
    style={'width': '100%', 'height': '800px'})

graph_layout = html.Div(
    id='graph_top_level',
    children=[
        dcc.Checklist(id='graph_options',
                      options=[{'label': 'Show models',
                                'value': 'show_models'},
                               {'label': 'Show properties',
                                'value': 'show_properties'}],
                      values=['show_properties'],
                      labelStyle={'display': 'inline-block'}),
        html.Div(id='graph_explorer',
                 children=[graph_component])])

layout_menu = html.Div(
    children=[dcc.Link('Explore Graph', href='/graph'),
              html.Span(' • '),
              dcc.Link('All Symbols', href='/property'),
              html.Span(' • '),
              dcc.Link('All Models', href='/model'),
              html.Span(' • '),
              dcc.Link('Explore with Materials Project', href='/load_material'),
              ])

# home page
home_manifesto = """
**Under active development, pre-alpha.**
Real materials are complex. In the field of Materials Science, 
we often rely on empirical relationships and rules-of-thumb to 
provide insights into the behavior of materials. This project
is designed to codify our knowledge of these empirical models 
and the relationships between them, along with providing tested, 
unit-aware implementations of each model.

When given a set of known properties of a material, the knowledge 
graph can help derive additional properties automatically. 
Integration with the [Materials Project](https://materialsproject.org) 
and other databases provides these sets of initial properties for 
a given material, as well as information on the real world 
distributions of these properties.

We also provide interfaces to machine-learned models. Machine 
learning is **great**, and one day might replace our conventional 
wisdom, but until then as scientists we still need to understand 
how to use and interpret these machine-learned models. 
Additionally, formally codifying our existing models will help 
train further machine-learned models in the future.
"""

graph_log = """
```
Graph initialization log:
{}
```
""".format(log_stream.getvalue())

index = html.Div([html.Br(),
                  dcc.Markdown(home_manifesto),
                  dcc.Markdown(graph_log)])

# header
app.layout = html.Div(
    children=[route,
              html.Div([html.H3(app.title), layout_menu, html.Br()],
                       style={'textAlign': 'center'}),
              html.Div(id='page-content'),
              # hidden table to make sure table component loads
              # (Dash limitation; may be removed in future)
              html.Div(children=[dt.DataTable(rows=[{}]), graph_layout],
                       style={'display': 'none'})],
    style={'marginLeft': 200, 'marginRight': 200, 'marginTop': 30})

# standard Dash css, fork this for a custom theme
# we real web devs now
app.css.append_css(
    {'external_url': 'https://codepen.io/mkhorton/pen/zPgJJw.css'})
# app.css.append_css(
#     {'external_url': 'https://codepen.io/montoyjh/pen/YjPKae.css'})
app.css.append_css(
    {'external_url': 'https://codepen.io/mikesmith1611/pen/QOKgpG.css'})


@app.callback(Output('material-content', 'children'),
              [Input('submit-formula', 'n_clicks'),
               Input('derive-properties', 'n_clicks')],
              [State('formula-input', 'value'),
               State('aggregate', 'values')])
def retrieve_material(n_clicks, n_clicks_derive, formula, aggregate):
    """
    Gets the material view from options

    Args:
        n_clicks (int): load material click
        n_clicks_derive (int): derive material properties
        formula (string): formula to find
        aggregate (bool): whether or not to aggregate derived properties

    Returns:
        Div of graph component with fulfilled options

    """

    mpid = mpr.get_mpid_from_formula(formula)
    material = mpr.get_material_for_mpid(mpid)

    if n_clicks is None:
        return ""

    if not material:
        return "Material not found."

    p = Graph()
    p.add_material(material)
    g = p.graph

    if n_clicks_derive is not None:
        p.evaluate()

    new_qs = {}
    if aggregate:
        new_qs = material.get_aggregated_quantities()

    rows = []
    for node in material.get_quantities():
        if node.symbol.category != 'object':
            if str(node.symbol.name) not in new_qs:
                rows.append(
                    {
                        'Symbol': str(node.symbol.name),
                        'Value': str(node.value),
                        'Units': str(node.symbol.unit_as_string)
                    }
                )

    # demo hack
    for symbol, quantity in new_qs.items():
        rows.append(
            {
                'Symbol': str(symbol),
                'Value': str(quantity.value),
            # TODO: node.node_value.value? this has to make sense
                # 'Units': str(node.node_value.symbol.unit_as_string)
            }
        )

    table = dt.DataTable(
        rows=rows,
        row_selectable=True,
        filterable=True,
        sortable=True,
        selected_row_indices=[],
        id='datatable'
    )

    material_graph_data = graph_conversion(
        g, nodes_to_highlight_green=material.get_quantities())
    options = AESTHETICS['global_options']
    options['edges']['color'] = '#000000'
    material_graph_component = html.Div(GraphComponent(
        id='material-graph',
        graph=material_graph_data,
        options=options
    ), style={'width': '100%', 'height': '400px'})

    return html.Div([
        html.H3('Graph'),
        material_graph_component,
        html.H3('Table'),
        table
    ])


material_layout = html.Div([
    dcc.Input(
        placeholder='Enter a formula...',
        type='text',
        value='',
        id='formula-input'
    ),
    html.Button('Load Material', id='submit-formula'),
    html.Button('Derive Properties', id='derive-properties'),
    dcc.Checklist(
        id='aggregate',
        options=[
            {'label': 'Aggregate Derived Properties', 'value': 'aggregate'}
        ],
        values=['aggregate'],
        labelStyle={'display': 'inline-block'}
    ),
    html.Br(),
    html.Br(),
    html.Div(id='material-content')
])


# routing, current routes defined are:
# / for home page
# /model for model summary
# /model/model_name for information on that model
# /property for property summary
# /property/property_name for information on that property
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    """

    Args:
      pathname:

    Returns:

    """

    path_info = parse_path(pathname)

    if path_info:
        if path_info['mode'] == 'model':
            if path_info['value']:
                return model_layout(path_info['value'])
            else:
                return models_index
        elif path_info['mode'] == 'property':
            if path_info['value']:
                property_name = path_info['value']
                return symbol_layout(property_name)
            else:
                return symbols_index()
        elif path_info['mode'] == 'load_material':
            return material_layout
        elif path_info['mode'] == 'graph':
            return graph_layout
        else:
            return '404'
    else:
        return index


if __name__ == '__main__':
    app.run_server(debug=True)
