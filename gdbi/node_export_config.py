from typing import List

class NodeExportConfig:
    """
    parameters
    ----------
    label_name: str
        The name of node type
    x_property_names: List[str]
        Optional, the attribute name corresponding to the node feature
    y_property_names: List[str]
        Optional, the attribute name corresponding to the node label
    """
    def __init__(self, label_name: str,
                 x_property_names: List[str] = None,
                 y_property_names: List[str] = None):
        self.label_name = label_name
        self.x_property_names = x_property_names
        self.y_property_names = y_property_names
