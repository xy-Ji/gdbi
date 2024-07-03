from neo4j import GraphDatabase
import torch
from typing import List, Dict
from gdbi import NodeExportConfig, EdgeExportConfig

class Neo4jInterface:
    
    def GraphDBConnection(self, graph_address, user_name, password):
        self.driver = GraphDatabase.driver(graph_address, auth=(user_name, password))
        return self.driver
    
    def get_graph(self, conn: GraphDBConnection,
                  graph_name: str, 
                  node_export_config: List[NodeExportConfig], 
                  edge_export_config: List[EdgeExportConfig]) -> Dict:
        with conn.session() as session:
            X_dict = dict()
            edge_index_dict = {}
            edge_attr_dict = {}
            Y_dict = {}
            pos_dict = {}
        
            for node_config in node_export_config:
                node_name = graph_name + "_" + node_config.label_name
                query = f"MATCH (node: {node_name}) RETURN node order by node.ID"
                node_result = session.run(query)
                X = list()
                Y = list()
                
                for record in node_result:
                    if node_config.x_property_names is not None:
                        if len(node_config.x_property_names) > 1:
                            node_feature = list()
                            for feature_name in node_config.x_property_names:
                                feature_item = str(record['node'][feature_name]).replace("[", "").replace("]", "").replace(",", " ").split()
                                node_feature.append([float(i) for i in feature_item])
                            X.append(node_feature)
                        else:
                            feature_item = str(record['node'][node_config.x_property_names[0]]).replace("[", "").replace("]", "").replace(",", " ").split()
                            X.append([float(i) for i in feature_item])
                    if node_config.y_property_names is not None:
                        if len(node_config.y_property_names) > 1:
                            label = list()
                            for label_name in node_config.y_property_names:
                                label.append(float(record['node'][label_name]))
                            Y.append(label)
                        else:
                            Y.append(float(record['node'][node_config.y_property_names[0]]))
                X_dict.update({node_config.label_name: torch.tensor(X)})     
                Y_dict.update({node_config.label_name: torch.tensor(Y)})   
            
            for edge_config in edge_export_config:
                node1_name, node2_name = edge_config.src_dst_label
                node1_name = graph_name + "_" + node1_name
                node2_name = graph_name + "_" + node2_name
                edge_name = graph_name + "_" + edge_config.label_name     
                
                query = f"MATCH (src:{node1_name})-[edge:{edge_name}]->(dst:{node2_name}) RETURN src.ID, dst.ID, edge"
                edge_result = session.run(query)
                src_node = list()
                dst_node = list()
                edge_attr = list() 
                
                for record in edge_result:
                    src_node.append(int(record[0]))
                    dst_node.append(int(record[1]))
                    edge = record[2]
                    if edge_config.x_property_names is not None :
                        if len(edge_config.x_property_names) >1:
                            edge_feature = list()
                            for feature_name in edge_config.x_property_names:
                                feature_item = str(edge[edge_config.x_property_names]).replace("[", "").replace("]", "").replace(",", " ").split()
                                edge_feature.append([float(i) for i in feature_item])
                            edge_attr.append(edge_feature)
                        else:
                            feature_item = str(edge[edge_config.x_property_names[0]]).replace("[", "").replace("]", "").replace(",", " ").split()
                            edge_attr.append([float(i) for i in feature_item])
                
                edge_index = [src_node, dst_node]
                edge_index_dict.update({edge_config.label_name: torch.tensor(edge_index)})
                edge_attr_dict.update({edge_config.label_name: torch.tensor(edge_attr)})
                
            Graph = {
                'X_dict': X_dict,
                'edge_index_dict': edge_index_dict,
                'edge_attr_dict': edge_attr_dict,
                'Y_dict': Y_dict,
                'pos_dict': pos_dict
            }
            return Graph

    def match(self, graph_name: str,
              label_name: List[str] = [''],
              src_dst_label: (str, str) = None, 
              x_property_names: Dict = None, 
              y_property_names: Dict = None) -> List:
        with self.driver.session() as session:
            result_list = []
            if src_dst_label is None:
                for lname in label_name:
                    if lname == '':
                        query = "MATCH (n) "
                    else:
                        node_name = graph_name + '_' + lname
                        query = f"MATCH (n:{node_name}) "
                    if x_property_names is not None and y_property_names is not None:
                        query += "WHERE all(x in keys($x_property_names) WHERE n[x] = $x_property_names[x]) and all(y in keys($y_property_names) WHERE n[y] = $y_property_names[y]) "
                    elif x_property_names is not None:
                        query += "WHERE all(x in keys($x_property_names) WHERE n[x] = $x_property_names[x]) "
                    elif y_property_names is not None:
                        query += "WHERE all(y in keys($y_property_names) WHERE n[y] = $y_property_names[y]) "
                    query += "RETURN n"
                    result = session.run(query, parameters={'x_property_names': x_property_names, 'y_property_names': y_property_names})
                    for record in result:
                        node = record['n']
                        node_dict = {prop: value for prop, value in node.items()}
                        result_list.append(node_dict)

                for lname in label_name:
                    if lname == '':
                        query = f"MATCH (src)-[r]->(dst) "
                    else:
                        edge_name = graph_name + '_' + lname
                        query = f"MATCH (src)-[r:{edge_name}]->(dst) "
                    if x_property_names is not None and y_property_names is not None:
                        query += "WHERE all(x in keys($x_property_names) WHERE r[x] = $x_property_names[x]) and all(y in keys($y_property_names) WHERE r[y] = $y_property_names[y]) "
                    elif x_property_names is not None:
                        query += "WHERE all(x in keys($x_property_names) WHERE r[x] = $x_property_names[x]) "
                    elif y_property_names is not None:
                        query += "WHERE all(y in keys($y_property_names) WHERE r[y] = $y_property_names[y]) "
                    query += "RETURN r, src.ID, dst.ID"
                    result = session.run(query, parameters={'x_property_names': x_property_names, 'y_property_names': y_property_names})
                    for record in result:
                        edge = record['r']
                        edge_dict = {prop: value for prop, value in edge.items()}
                        edge_dict.update({'src': record['src.ID'], 'dst': record['dst.ID']})
                        result_list.append(edge_dict)
                        
            else:
                src, dst = src_dst_label
                src = graph_name + '_' + src
                dst = graph_name + '_' + dst
                for lname in label_name:
                    if lname == '':
                        query = f"MATCH (src:{src})-[r]->(dst:{dst}) "
                    else:
                        edge_name = graph_name + '_' + lname
                        query = f"MATCH (src:{src})-[r:{edge_name}]->(dst:{dst}) "
                    if x_property_names is not None and y_property_names is not None:
                        query += "WHERE all(x in keys($x_property_names) WHERE r[x] = $x_property_names[x]) and all(y in keys($y_property_names) WHERE r[y] = $y_property_names[y]) "
                    elif x_property_names is not None:
                        query += "WHERE all(x in keys($x_property_names) WHERE r[x] = $x_property_names[x]) "
                    elif y_property_names is not None:
                        query += "WHERE all(y in keys($y_property_names) WHERE r[y] = $y_property_names[y]) "
                    query += "RETURN r, src.ID, dst.ID"
                    result = session.run(query, parameters={'x_property_names': x_property_names, 'y_property_names': y_property_names})
                    for record in result:
                        edge = record['r']
                        edge_dict = {prop: value for prop, value in edge.items()}
                        edge_dict.update({'src': record['src.ID'], 'dst': record['dst.ID']})
                        result_list.append(edge_dict)
                        
            return result_list
        
    def write_property(self, graph_name: str, 
                       label_name: str, 
                       src_dst_label: (str, str) = None, 
                       property_name: str = None, 
                       property_values: Dict = None) -> bool:
        with self.driver.session() as session:
            label_name = graph_name + '_' + label_name
            if src_dst_label == None:
                for ID in property_values:
                    query = f"MATCH (n:{label_name}) WHERE n.ID = {ID} SET n.{property_name} = {property_values[ID]}"
                    result = session.run(query)
                    if not result.consume().counters._contains_updates:
                        query = f"CREATE (n:{label_name} {{ID: {ID}, {property_name}: {property_values[ID]}}})"
                        result = session.run(query)
                return True
                    
            else:
                for ID in property_values:
                    src, dst = src_dst_label
                    src = graph_name + '_' + src
                    dst = graph_name + '_' + dst
                    query = f"MATCH (src:{src} {{ID: {ID[0]}}})-[r:{label_name}]->(dst:{dst} {{ID: {ID[1]}}}) SET r.{property_name} = {property_values[ID]}"
                    result = session.run(query)
                    if not result.consume().counters._contains_updates:
                        query = f"MATCH (src:{src} {{ID: {ID[0]}}}), (dst:{dst} {{ID: {ID[1]}}}) CREATE (src)-[r:{label_name} {{{property_name}:{property_values[ID]}}}]->(dst)"
                        result = session.run(query)
                return True
