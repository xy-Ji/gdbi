# graphDBInterface

--------------------------------------------------------------------------------
The interface between the graph neural network computation framework and the graph database defines the methods and rules for data interaction between the framework and the graph database. The basic process of integrating the graph database as an external data source into the graph neural network framework can be summarized in the following steps:

* Connect the graph neural network framework to the database;
* Pull data from the graph database and construct graph data types supported by the graph neural network framework;
* Use modules such as sampling and message passing in the graph neural network framework for training/inference;
* Write back the obtained embeddings/prediction results to the graph database.
  
Additionally, considering that the graph neural network framework may want to retrieve information for specific parts of the graph rather than the entire graph, it is necessary to provide query interfaces for the graph database to meet the querying needs of the graph neural network framework.

Based on this, the graph database interface should mainly include the following modules:

* Graph Database Connection Interface: Implements the connection between the graph neural network computation framework and the graph database, enabling the computation framework to interact with the graph database through interfaces.

* Data Query Interface: Used to query and retrieve graph data from the graph database. These interfaces may include queries for specified nodes or edges, filtering data based on conditions, obtaining attribute information of nodes/edges, etc., and inputting them into the graph neural network framework.

* Data Retrieval Interface: Used to import data from the graph database into the computation framework for training and inference of graph neural network models. These interfaces can transform the data obtained from the graph database into a specified intermediate standard data format.

* Data Write-Back Interface: After the graph neural network computation, there may be a need to perform write-back operations on the data in the graph database, such as writing the training results back to the graph database. Therefore, the interface specification needs to define corresponding data write-back interfaces.

## Introduction to graph databases
### neo4j

**Database version** 
neo4j community 5.15.0

**Python driver installation**
   ```bash
   pip install neo4j==5.16.0
   ```

**Import csv files into graph database**
```
LOAD CSV WITH HEADERS FROM "file:///data.csv" AS row
CREATE (:graphname_labelname {ID: row.ID, ... });
```

Take the cora dataset as an example:
```
LOAD CSV WITH HEADERS FROM "file:///cora/cora_content.csv" AS row
CREATE (:cora_node {ID: toInteger(row.ID), label: toInteger(row.label), attr:row.attr });
```
```
LOAD CSV WITH HEADERS FROM 'file:///cora/cora_cites.csv' AS row
MATCH (from:cora_node {ID: toInteger(row.ID1)}), (to:cora_node {ID: toInteger(row.ID2)})
CREATE (from)-[r:cora_edge]→(to);
```
**Tips**
The neo4j community version does not support switching databases, so when naming nodes and relationships, add `graphname_` before `label_name.` to distinguish the dataset.

### NebulaGraph
**Database version**
 3.6.0
**Python driver installation**
```bash
pip install nebula3-python==3.4.0
```
**Tips**
When querying NebulaGraph database on attribute values, you need to set the index first, otherwise the query cannot be performed normally. The nGQL statement to add an index is as follows:
```
CREATE TAG INDEX IF NOT EXISTS index_label ON node(label);
```
### gStore

### AtlasGraph
AtlasGraph is the first domestically developed next-generation cloud-native real-time parallel graph database based on Rust.
AtlasGraph Homepage:[https://atlasgraph.io/](https://atlasgraph.io/)

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

Through the export configuration of nodes and edges, the entire graph or subgraph can be exported from the graph database.

#### Parameters

* **conn** *(GraphDBConnection)* - Graph database connection information.
* **graph_name** *(string)* - Graph name.
* **node_export_config** *(NodeExportConfig)* - The export configuration of nodes.
    **NodeExportConfig**
    * **labelname** *(string)* - The name of node type.
    * **x_property_names** *(List[string])* - The attribute name corresponding to the node feature.
    * **y_property_names** *(List[string])* - The attribute name corresponding to the node label.
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
* **y_property_names** *(Dict[string: value])* - The label names and their values of node or edge.


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
