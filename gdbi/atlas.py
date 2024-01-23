from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import atlas_connector
import numpy as np
from atlas_connector import AtlasClient as Builtin_AtlasClient
from atlas_connector import AtlasMapping as Builtin_AtlasMapping
from atlas_connector import ItemConfig as Builtin_ItemConfig
from google.protobuf.internal import containers as _containers

INCLUDE = "include"
EXCLUDE = "exclude"


class AtlasClient:
    def __init__(self, log_file_path: Path, meta_addr: str):
        self.atlas_client = Builtin_AtlasClient(str(log_file_path), meta_addr)


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


def write_vertex_value(
    atlas_client: AtlasClient,
    atlas_mapping: AltasMapping,
    graph_name: str,
    label_name: str,
    property_name: str,
    inner_ids: np.ndarray,
    values: np.ndarray,
) -> bool:
    return atlas_connector.write_vertex_value(
        atlas_client.atlas_client,
        atlas_mapping.rust_atlas_mapping,
        graph_name,
        label_name,
        property_name,
        inner_ids,
        values,
    )


def write_edge_value(
    atlas_client: AtlasClient,
    atlas_mapping: AltasMapping,
    graph_name: str,
    label_name: str,
    src_label_name: str,
    dst_label_name: str,
    property_name: str,
    inner_ids: np.ndarray,
    src_inner_ids: np.ndarray,
    dst_inner_ids: np.ndarray,
    values: np.ndarray,
) -> bool:
    return atlas_connector.write_edge_value(
        atlas_client.atlas_client,
        atlas_mapping.rust_atlas_mapping,
        graph_name,
        label_name,
        src_label_name,
        dst_label_name,
        property_name,
        inner_ids,
        src_inner_ids,
        dst_inner_ids,
        values,
    )
