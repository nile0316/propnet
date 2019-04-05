import logging

from os import path

from propnet.core.symbols import Symbol
from propnet.core.models import Model

from monty.serialization import loadfn
import networkx as nx

# noinspection PyUnresolvedReferences
import propnet.models
from propnet.core.registry import Registry

log = logging.getLogger(__name__)
AESTHETICS = loadfn(path.join(path.dirname(__file__), 'aesthetics.yaml'))
STYLESHEET = loadfn(path.join(path.dirname(__file__), 'graph_stylesheet.yaml'))

# TODO: use the attributes of the graph class, rather than networkx
def graph_conversion(graph: nx.DiGraph,
                     graph_size_pixels=800,
                     nodes_to_highlight_green=(),
                     nodes_to_highlight_yellow=(),
                     nodes_to_highlight_red=(),
                     hide_unconnected_nodes=True,
                     aesthetics=None):
    """Utility function to render a networkx graph
    from Graph.graph for use in GraphComponent

    Args:
        graph (networkx.graph): from Graph.graph

    Returns: graph dict
    """

    node_xy = nx.drawing.layout.kamada_kawai_layout(graph, scale=graph_size_pixels)

    nodes = []
    edges = []

    for n in graph.nodes():
        x_pos, y_pos = node_xy[n]

        # should do better parsing of nodes here
        # TODO: this is also horrific code for demo, change
        # TODO: more dumb crap related to graph
        if isinstance(n, Symbol):
            # property
            name = n.name
            label = n.display_names[0]
            node_type = 'symbol'
        elif isinstance(n, Model):
            # model
            name = n.title
            label = n.title
            node_type = 'model'
        else:
            name = None
            label = None
            node_type = None

        if name:
            # Get node, labels, name, and title
            node = {
                'data': {'id': name,
                         'label': label
                         },
                'position': {'x': x_pos,
                             'y': y_pos
                             },
                'locked': False,
                'classes': node_type
            }

            if node_type == 'model':
                node['classes'] += " labeloff"
            else:
                node['classes'] += " labelon"
            '''
            if node.get("show_labels"):
                node.update({"label": label,
                             # "title": label,
                             "shape": "box",
                             "font": {"color": "#ffffff",
                                      "face": "Helvetica",
                                      "size": 20},
                             "size": 30})
            # Pop labels if they exist
            else:
                node.update({"size": 8.0,
                             "shape": "diamond",
                             "label": "",
                             "title": ""})
            '''

            nodes.append(node)
    '''
    log.info("Nodes to highlight green: {}".format(
            nodes_to_highlight_green))
    highlight_nodes = any([nodes_to_highlight_green, nodes_to_highlight_yellow,
                           nodes_to_highlight_red])
    if highlight_nodes:
        log.debug("Nodes to highlight green: {}".format(
            nodes_to_highlight_green))
        for node in nodes:
            if node['id'] in nodes_to_highlight_green:
                node['color'] = '#9CDC90'
            elif node['id'] in nodes_to_highlight_yellow:
                node['color'] = '#FFBF00'
            elif node['id'] in nodes_to_highlight_red:
                node['color'] = '#FD9998'
            else:
                node['color'] = '#BDBDBD'
    '''

    connected_nodes = set()

    # TODO: need to clean up after model refactor
    def get_node_id(node_):
        return node_.title if isinstance(node_, Model) else node_.name

    for n1, n2 in graph.edges():
        id_n1 = get_node_id(n1)
        id_n2 = get_node_id(n2)

        if id_n1 and id_n2:
            connected_nodes.add(id_n1)
            connected_nodes.add(id_n2)
            edges.append({'data': {'source': id_n1, 'target': id_n2}},)

    if hide_unconnected_nodes:
        nodes = [n for n in nodes if n['data']['id'] in connected_nodes]

    graph_data = nodes + edges

    return graph_data


def parse_path(pathname):
    """Utility function to parse URL path for routing purposes etc.
    This function exists because the path has to be parsed in
    a few places for callbacks.

    Args:
      pathname (str): path from url

    Returns:
        (dict) dictionary containing 'mode' ('property', 'model' etc.),
        'value' (name of property etc.)

    """

    if pathname == '/' or pathname is None:
        return None

    mode = None  # 'property' or 'model'
    value = None  # property name / model name

    # TODO: get rid of this

    if pathname == '/model':
        mode = 'model'
    elif pathname.startswith('/model'):
        mode = 'model'
        for model in Registry("models").keys():
            if pathname.startswith('/model/{}'.format(model)):
                value = model
    elif pathname == '/property':
        mode = 'property'
    elif pathname.startswith('/property'):
        mode = 'property'
        for property_ in Registry("symbols").keys():
            if pathname.startswith('/property/{}'.format(property_)):
                value = property_
    elif pathname.startswith('/explore'):
        mode = 'explore'
    elif pathname.startswith('/plot'):
        mode = 'plot'
    elif pathname.startswith('/generate'):
        mode = 'generate'
    elif pathname.startswith('/correlate'):
        mode = 'correlate'
    elif pathname.startswith('/home'):
        mode = 'home'

    return {
        'mode': mode,
        'value': value
    }
