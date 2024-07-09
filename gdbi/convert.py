from typing import Dict
import torch

def graph2ggl(graph: Dict):
    from gammagl.data import Graph, HeteroGraph
    if len(graph['X_dict']) == 1 and len(graph['edge_index_dict']) == 1:
        x = torch.Tensor(list(graph['X_dict'].values()))
        y = torch.Tensor(list(graph['Y_dict'].values()))
        edge_index = list(graph['edge_index_dict'].values())[0]
        edge_attr = list(graph['edge_attr_dict'].values())[0]
        return Graph(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    
    else:
        data = HeteroGraph()
        for name, feature in graph['X_dict'].items():
            data[name].x = torch.Tensor(feature)
        for name, label in graph['Y_dict'].items():
            data[name].y = torch.Tensor(label)
        for name, edge_index in graph['edge_index_dict'].items():
            data[name].edge_index = edge_index
        for name, edge_attr in graph['edge_attr_dict'].items():
            data[name].edge_attr = edge_attr
        return data
    
def graph2pyg(graph: Dict):
    from torch_geometric.data import Data, HeteroData
    if len(graph['X_dict']) == 1 and len(graph['edge_index_dict']) == 1:
        x = torch.Tensor(list(graph['X_dict'].values()))
        y = torch.Tensor(list(graph['Y_dict'].values()))
        edge_index = list(graph['edge_index_dict'].values())[0]
        edge_attr = list(graph['edge_attr_dict'].values())[0]
        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y)
    
    else:
        data = HeteroData()
        for name, feature in graph['X_dict'].items():
            data[name].x = torch.Tensor(feature)
        for name, label in graph['Y_dict'].items():
            data[name].y = torch.Tensor(label)
        for name, edge_index in graph['edge_index_dict'].items():
            data[name].edge_index = edge_index
        for name, edge_attr in graph['edge_attr_dict'].items():
            data[name].edge_attr = edge_attr
        return data

def graph2dgl(graph: Dict):
    from dgl import DGLGraph, DGLHeteroGraph
    if len(graph['X_dict']) == 1 and len(graph['edge_index_dict']) == 1:
        x = torch.Tensor(list(graph['X_dict'].values()))
        y = torch.Tensor(list(graph['Y_dict'].values()))
        edge_index = list(graph['edge_index_dict'].values())[0]
        edge_attr = list(graph['edge_attr_dict'].values())[0]
        g = DGLGraph()
        g.add_nodes(x.shape[0])
        g.ndata['x'] = x
        g.edata['edge_index'] = edge_index
        g.edata['edge_attr'] = edge_attr
        g.ndata['y'] = y
        return g
    
    else:
        data = DGLHeteroGraph()
        for name, feature in graph['X_dict'].items():
            data.nodes[name].data['x'] = torch.Tensor(feature)
        for name, label in graph['Y_dict'].items():
            data.nodes[name].data['y'] = torch.Tensor(label)
        for name, edge_index in graph['edge_index_dict'].items():
            data.edges[name].data['edge_index'] = edge_index
        for name, edge_attr in graph['edge_attr_dict'].items():
            data.edges[name].data['edge_attr'] = edge_attr
        return data