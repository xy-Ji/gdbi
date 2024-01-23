# graphDBInterface

--------------------------------------------------------------------------------
## Environment Settings
**neo4j**

Database version: neo4j community 5.15.0
   ```
   python==3.9.18
   neo4j==5.16.0
   torch==2.1.2
   ```

## Functions

### GraphDBConnection

```
GraphDBConnection(graph_address, user_name, password)
```

Graph database connection interface. Pulling data from a graph database requires maintaining a connection to the graph database.

#### Parameters

* **graph_address** *(str)* - The address of graph database.
* **user_name** *(str)* - Usermame.
* **password** *(str)* - Password.


### get_graph

```
get_graph(conn, graph_name, node_export_config, edge_export_config) -> (Graph)
```

Through the export configuration of nodes and edges, the graph data structure in the graph neural network framework can be exported from the graph database.

#### Parameters

* **conn** *(GraphDBConnection)* - Graph database connection information.
* **graph_name** *(string)* - Graph name.
* **node_export_config** *(NodeExportConfig)* - The export configuration of nodes.
    **NodeExportConfig**
    * **labelname** *(string)* - The name of node type.
    * **x_property_names** *(List[string])* - The attribute name corresponding to the edge feature.
    * **y_property_names** *(List[string])* - The attribute name corresponding to the edge label.
* **edge_export_config** *(EdgeExportConfig)* - The export configuration of edges.
    **EdgeExportConfig**
    * **labelname** *(string)* - The name of edge type.
    * **src_dst_label** *((string, string))* - The type of source node and destination node.
    * **x_property_names** *(List[string])* - The attribute name corresponding to the edge feature.
    * **y_property_names** *(List[string])* - The attribute name corresponding to the edge label.

#### Returns

* **graph** *(Graph)* - Graph data for graph neural network framework.
    **Graph**
    * **X_dict** *(Dict[string: tensor])* - The dictionary of node feature matric.
    * **edge_index_dict** *(Dict[string: tensor])* - The dictionary of edge index.
    * **edge_attr_dict** *(Dict[string: tensor])* - The dictionary of edge attribute matric.
    * **Y_dict** *(Dict[string: tensor])* - The dictionary of node label.
    * **pos_dict** *(Dict[string: tensor])* - The dictionary of node position.

### match

```
match(graph_name, label_name, src_dst_label, x_property_names, y_property_names) -> (ID)
```

Query interface. Used to query the graph database and obtain graph data information.

#### Parameters

* **graph_name** *(string)* - Graph name.
* **label_name** *(string)* - The type of node or edge.
* **src_dst_label** *((string, string))* - The type of source node and destination node.
* **x_property_names** *(Dict[string: value])* - The property names and their values of node or edge.
* **x_property_names** *(Dict[string: value])* - The label names and their values of node or edge.


#### Returns

* **ID** *(List[])* - The unique identifier of the node or edge.


### write_property

```
write_property(graph_name, label_name, src_dst_label, property_name, property_values) -> (success)
```

Writeback interface. After getting the trained embedding or completing inference, the results need to be written back to the graph database.

#### Parameters

* **graph_name** *(string)* - Graph name.
* **label_name** *(string)* - The type of node or edge.
* **src_dst_label** *((string, string))* - The type of source node and destination node.
* **property_name** *(string)* - The property name to be written back.
* **property_values** *(Dict[int: value])* - The ID and corresponding value to be written back.


#### Returns

* **success** *(bool)* - Write success flag.
