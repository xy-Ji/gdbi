from typing import List

class EdgeExportConfig:
    """
    parameters
    ----------
    label_name: str
        The name of edge type
    src_dst_label: (str, str)
        The type of source node and destination node
    x_property_names: List[str]
        Optional, the attribute name corresponding to the edge feature
    y_property_names: List[str]
        Optional, the attribute name corresponding to the edge label
    """
    def __init__(self, label_name: str,
                 src_dst_label: (str,str),
                 x_property_names: List[str] = None,
                 y_property_names: List[str] = None):
        self.label_name = label_name
        self.src_dst_label = src_dst_label
        self.x_property_names = x_property_names
        self.y_property_names = y_property_names