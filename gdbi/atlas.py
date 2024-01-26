from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import atlas_connector
import numpy as np
from atlas_connector import AtlasClient as Builtin_AtlasClient
from atlas_connector import AtlasMapping as Builtin_AtlasMapping
from atlas_connector import ItemConfig as Builtin_ItemConfig
from google.protobuf.internal import containers as _containers
from atlas_gnn.graph.generate_graph import write_vertex_value, write_edge_value
from atlas_gnn.graph.graph_collection import match_node, match_edge
from typing import Set
import torch as th

INCLUDE = "include"
EXCLUDE = "exclude"


class AtlasClient:
    def __init__(self, log_file_path: Path, meta_addr: str, user: str, password: str):
        self.atlas_client = Builtin_AtlasClient(str(log_file_path), meta_addr, user, password)


class VertexConfig:
    def __new__(
        cls,
        vertex_label_name: str,
        propertyStatus: str = INCLUDE,
        properties: Union[
            _containers.RepeatedScalarFieldContainer[str], List[str]
        ] = [],
        target_property: Optional[str] = None,
    ) -> Builtin_ItemConfig:
        return Builtin_ItemConfig(
            vertex_label_name, [], propertyStatus, properties, target_property
        )


class EdgeConfig:
    def __new__(
        cls,
        edge_label_name: str,
        src_dst_limits: List[Tuple[str, str]],
        propertyStatus: str = INCLUDE,
        properties: Union[
            _containers.RepeatedScalarFieldContainer[str], List[str]
        ] = [],
        target_property: Optional[str] = None,
    ) -> Builtin_ItemConfig:
        return Builtin_ItemConfig(
            edge_label_name, src_dst_limits, propertyStatus, properties, target_property
        )


class AltasMapping:
    def __init__(self, rust_atlas_mapping: Builtin_AtlasMapping):
        self.rust_atlas_mapping = rust_atlas_mapping
        self.vertex_id2pk_map: Dict[str, Tuple[bool, List[str]]] = {}
        self.edge_id2pk_map: Dict[Tuple[str, str, str], Tuple[bool, List[str]]] = {}

    def get_vertex_num(self, label_name: str) -> int:
        return self.rust_atlas_mapping.get_vertex_num(label_name)

    def get_edge_num(self, label_name: Tuple[str, str, str]) -> int:
        return self.rust_atlas_mapping.get_edge_num(label_name)

    def get_vertex_id2pk(self, label_name: str) -> Tuple[bool, List[str]]:
        if label_name in self.vertex_id2pk_map:
            return self.vertex_id2pk_map[label_name]
        self.vertex_id2pk_map[label_name] = self.rust_atlas_mapping.get_vertex_id2pk(
            label_name
        )
        return self.vertex_id2pk_map[label_name]

    def get_edge_id2pk(
        self, label_name: Tuple[str, str, str]
    ) -> Tuple[bool, Union[List[str], List[int]]]:
        if label_name in self.edge_id2pk_map:
            return self.edge_id2pk_map[label_name]
        self.edge_id2pk_map[label_name] = self.rust_atlas_mapping.get_edge_id2pk(
            label_name
        )
        return self.edge_id2pk_map[label_name]


def load_graph(
    atlas_client: AtlasClient,
    graph_name: str,
    project_name: str,
    export_batch_size: int,
    export_queue_size: int,
    vertices: List[VertexConfig],
    edges: List[EdgeConfig],
    as_homo_graph: bool = False,
    vertex_label: str = "Vertex",
    edge_label: str = "Edge",
) -> Tuple[
    Dict[Tuple[str, str, str], Tuple[np.ndarray, np.ndarray]],      
    Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]],            
    Tuple[                                                          
        Dict[Tuple[str, str, str], np.ndarray], Dict[Tuple[str, str, str], np.ndarray]
    ],
    AltasMapping,
]:
    (
        graph_data,
        (vertex_labels_map, vertex_feats_map),
        (edge_labels_map, edge_feats_map),
        rust_atlas_mapping,
    ) = atlas_connector.load_graph(
        atlas_client.atlas_client,
        graph_name,
        project_name,
        export_batch_size,
        export_queue_size,
        vertices,
        edges,
        as_homo_graph,
        vertex_label,
        edge_label,
    )
    atlas_mapping = AltasMapping(rust_atlas_mapping)
    return (
        graph_data,
        (vertex_labels_map, vertex_feats_map),
        (edge_labels_map, edge_feats_map),
        atlas_mapping,
    )

class AtlasInterface:

    def GraphDBConnection(self, graph_address, user_name, password):
        self.atlas_client = AtlasClient(log_file_path=Path("./atlas_gnn.log"), meta_addr=graph_address, user=user_name, password=password)
        return self.atlas_client

    def get_graph(self, conn: AtlasClient, graph_name: str, node_export_config: List[VertexConfig], edge_export_config: List[EdgeConfig]):
        
        X = {}
        edge_index = {}
        edge_attr = {}
        Y = {}
        pos_dict = {}

        (
        graph_data,
        (vertex_labels_map, vertex_feats_map),
        (edge_labels_map, edge_feats_map),
        atlas_mapping,
        ) = load_graph(
        atlas_client=conn,
        graph_name=graph_name,
        project_name=graph_name,
        export_batch_size=1024,
        export_queue_size=512,
        vertices=node_export_config,
        edges=edge_export_config,
        )

        X = vertex_feats_map
        Y = vertex_labels_map
        edge_attr = edge_feats_map
        edge_index = graph_data

        Graph = {
            'X_dict': X,
            'edge_index_dict': edge_index,
            'edge_attr_dict': edge_attr,
            'Y_dict': Y,
            'pos_dict': pos_dict
        }

        return Graph

    def match(self, graph_name: str, label_name: List[str] = [''], src_dst_label: (str, str) = None, x_property_names: Dict = None, y_property_names: Dict = None):
        atlas_graph = self.atlas_client
        if src_dst_label is None:
            result = match_node(atlas_graph, graph_name, label_name, x_property_names, y_property_names)
        else:
            result = match_edge(atlas_graph, graph_name, label_name,src_dst_label, x_property_names, y_property_names)

        return result
            

    def write_property(self, graph_name: str, label_name: List[str] = [''], src_dst_label: (str, str) = None, property_names: str = None, property_value: Dict = None):
        atlas_graph = self.atlas_client
        if src_dst_label is None:
            write_vertex_value(atlas_graph, graph_name, label_name, property_names, property_value)
        else:
            write_edge_value(atlas_graph, graph_name, label_name, src_dst_label, property_names, property_value)


        

