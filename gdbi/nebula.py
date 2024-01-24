from typing import Optional, List, Dict
from nebula3.gclient.net import Connection
from nebula3.gclient.net.SessionPool import SessionPool
from nebula3.Config import SessionPoolConfig
import re
import torch
import numpy as np
from node_export_config import NodeExportConfig
from edge_export_config import EdgeExportConfig

class NebulaInterface():
    def __init__(self):
        super().__init__()
        self.connection_database = None
        self.connection_graph = None

    def GraphDBConnection(self, graph_address: str, user_name: str, password: str):
        self.graph_address = graph_address
        self.user_name = user_name
        self.password = password
        conn = Connection()
        conn.open(graph_address.split(":")[0], int(graph_address.split(":")[1]), 1000)
        auth_result = conn.authenticate(user_name, password)
        assert auth_result.get_session_id() != 0
        self.connection_database = conn
        return conn

    def _get_attr_value(self, query: str):
        res = self.connection_graph.execute(query)
        if res.is_empty():
            raise ValueError("Query result is empty. Query: %s" % query)
        res = res.column_values('RESULT')
        result_list = []
        for record in res:
            record_str = str(record)
            if record_str == "__NULL__":
                result_list.append(-1)
            elif '.' in record_str and ' ' in record_str:
                result_list.append(list(map(float, record_str.replace('"', '').split())))
            elif '.' not in record_str and ' ' in record_str:
                result_list.append(list(map(int, record_str.replace('"', '').split())))
            elif '.' in record_str and ' ' not in record_str:
                result_list.append(float(record_str.replace('"', '')))
            else:
                result_list.append(int(record_str.replace('"', '')))
        return result_list

    def get_graph(
            self, conn: GraphDBConnection,
            graph_name: str,
            node_export_config: Optional[List[NodeExportConfig]] = None,
            edge_export_config: Optional[List[EdgeExportConfig]] = None,
    ):
        if self.connection_graph == None:
            config = SessionPoolConfig()
            self.connection_graph = SessionPool(self.user_name, self.password, graph_name,
                                                [(self.graph_address.split(":")[0],
                                                  int(self.graph_address.split(":")[1]))])
            assert self.connection_graph.init(config)

        if node_export_config == None:
            node_export_config = []
            describe_tags_query = "SHOW TAGS"
            tags_result = self.connection_graph.execute(describe_tags_query)
            all_tags = [str(tag).replace('"', '') for tag in tags_result]
            for tag in all_tags:
                node_config = NodeExportConfig(tag)
                node_x_properties = []
                node_y_properties = []
                describe_tag_query = f"DESCRIBE TAG {tag}"
                attributes_result = self.connection_graph.execute(describe_tag_query)
                if attributes_result.is_empty():
                    node_export_config.append(node_config)
                    continue
                for attr in attributes_result:
                    attr_name = str(attr.get_value_by_key("Field")).replace('"', '')
                    if attr_name[0] == 'y':
                        node_y_properties.append(attr_name)
                    else:
                        node_x_properties.append(attr_name)
                node_config.x_property_names = node_x_properties
                node_config.y_property_names = node_y_properties
                node_export_config.append(node_config)
        if edge_export_config == None:
            edge_export_config = []
            query = "SHOW EDGES"
            result = self.connection_graph.execute(query)
            if not result.is_empty():
                edge_types = [str(edge).replace('"', '') for edge in result]
                for edge_type in edge_types:
                    edge_config = EdgeExportConfig(edge_type)
                    edge_x_properties = []
                    edge_y_properties = []
                    query = f"MATCH (v1)-[e:{edge_type}]->(v2) RETURN id(v1), id(v2) LIMIT 1;"
                    result = self.connection_graph.execute(query)
                    result_list = [str(record) for record in result.row_values(0)]
                    node_type = []
                    for record in result_list:
                        query = f"MATCH (v) WHERE id(v) == {record} RETURN v;"
                        result = self.connection_graph.execute(query)
                        values = result.row_values(0)
                        value_str = str(values)
                        start_char = ":"
                        end_char = "{"
                        node_type.append(
                            re.search(f'{re.escape(start_char)}(.*?){re.escape(end_char)}', value_str).group(0).replace(
                                ':',
                                '').replace(
                                '{', ''))
                    edge_config.src_dst_label = tuple(node_type)
                    describe_edge_query = f"DESCRIBE EDGE {edge_type}"
                    attributes_result = self.connection_graph.execute(describe_edge_query)
                    if attributes_result.is_empty():
                        edge_export_config.append(edge_config)
                        continue
                    for attr in attributes_result:
                        attr_name = str(attr.get_value_by_key("Field")).replace('"', '')
                        if attr_name[0] == 'y':
                            edge_y_properties.append(attr_name)
                        else:
                            edge_x_properties.append(attr_name)
                    edge_config.x_property_names = edge_x_properties
                    edge_config.y_property_names = edge_y_properties
                    edge_export_config.append(edge_config)
        X_dict = {}
        edge_index_dict = {}
        edge_attr_dict = {}
        Y_dict = {}
        pos_dict = {}
        for node_config in node_export_config:
            table_name = node_config.label_name
            node_x_values = None
            for attr_name in node_config.x_property_names:
                match_clause = "MATCH (item:%s)" % table_name
                return_clause = "RETURN item.%s.%s AS RESULT, id(item) AS ID ORDER BY ID" % (table_name, attr_name)
                query = "%s %s" % (match_clause, return_clause)
                result = self._get_attr_value(query)
                if node_x_values == None:
                    node_x_values = np.array(result)
                else:
                    node_x_values = np.concatenate((node_x_values, np.array(result)), axis=1)
            node_y_values = None
            for attr_name in node_config.y_property_names:
                match_clause = "MATCH (item:%s)" % table_name
                return_clause = "RETURN item.%s.%s AS RESULT, id(item) AS ID ORDER BY ID" % (table_name, attr_name)
                query = "%s %s" % (match_clause, return_clause)
                result = self._get_attr_value(query)
                if node_y_values == None:
                    node_y_values = np.array(result)
                else:
                    node_y_values = np.concatenate((node_y_values, np.array(result)), axis=1)
            if node_x_values is not None:
                X_dict[table_name] = torch.Tensor(node_x_values)
            if node_y_values is not None:
                Y_dict[table_name] = torch.Tensor(node_y_values).to(torch.int64)

        for edge_config in edge_export_config:
            edge_type = edge_config.label_name
            edge_x_values = None
            for attr_name in edge_config.x_property_names:
                match_clause = "MATCH() - [item: %s]->()" % edge_type
                return_clause = "RETURN item.%s AS RESULT, item.id AS ID ORDER BY ID" % attr_name
                query = "%s %s" % (match_clause, return_clause)
                result = self._get_attr_value(query)
                if edge_x_values == None:
                    edge_x_values = np.array(result)
                else:
                    edge_x_values = np.concatenate((edge_x_values, np.array(result)), axis=1)
            edge_y_values = None
            for attr_name in edge_config.y_property_names:
                match_clause = "MATCH() - [item: %s]->()" % edge_type
                return_clause = "RETURN item.%s AS RESULT, item.id AS ID ORDER BY ID" % attr_name
                query = "%s %s" % (match_clause, return_clause)
                result = self._get_attr_value(query)
                if edge_y_values == None:
                    edge_y_values = np.array(result)
                else:
                    edge_y_values = np.concatenate((edge_y_values, np.array(result)), axis=1)
            if edge_x_values is not None:
                edge_attr_dict[edge_type] = torch.Tensor(edge_x_values[0])
            if edge_y_values is not None:
                Y_dict[edge_type] = torch.Tensor(edge_y_values[0]).to(torch.int64)
        for edge_config in edge_export_config:
            edge_index_part = []
            edge_type = edge_config.label_name
            query = f"MATCH (v1)-[e:{edge_type}]->(v2) RETURN id(v1) AS SID, id(v2) AS DID ORDER BY SID, DID;"
            result = self.connection_graph.execute(query)
            s = list(map(int, map(str, result.column_values('SID'))))
            d = list(map(int, map(str, result.column_values('DID'))))
            edge_index_part.append(s)
            edge_index_part.append(d)
            edge_index_dict[edge_type] = torch.Tensor(edge_index_part).to(torch.int64)
        Graph = {
            'X_dict': X_dict,
            'edge_index_dict': edge_index_dict,
            'edge_attr_dict': edge_attr_dict,
            'Y_dict': Y_dict,
            'pos_dict': pos_dict
        }
        return Graph

    def _get_where(self, s, x_property_names, y_property_names):
        query = "WHERE "
        if x_property_names is None and y_property_names is None:
            return ""
        if x_property_names is not None:
            for name, value in x_property_names.items():
                query += f"{s}.{name} == {value} and "
        if y_property_names is not None:
            for name, value in y_property_names.items():
                query += f"{s}.{name} == {value} and "
        return query[:-4]

    def match(self, graph_name: str,
              label_name: List[str] = [''],
              src_dst_label: (str, str) = None,
              x_property_names: Dict = None,
              y_property_names: Dict = None
              ) -> List:
        if self.connection_graph == None:
            config = SessionPoolConfig()
            self.connection_graph = SessionPool(self.user_name, self.password, graph_name,
                                                [(self.graph_address.split(":")[0],
                                                  int(self.graph_address.split(":")[1]))])
            assert self.connection_graph.init(config)
        result_list = []
        if src_dst_label is None:
            for lname in label_name:
                if lname == '':
                    query = "MATCH (item) "
                else:
                    query = f"MATCH (item:{lname}) "
                query += self._get_where(f"item.{lname}", x_property_names, y_property_names)
                query += "RETURN id(item)"
                print(query)
                result = self.connection_graph.execute(query)
                res = result.column_values('id(item)')
                for record in res:
                    result_list.append(int(str(record).replace('"', '')))
            for lname in label_name:
                if lname == '':
                    query = f"MATCH (src)-[r]->(dst) "
                else:
                    query = f"MATCH (src)-[r:{lname}]->(dst) "
                query += self._get_where("r", x_property_names, y_property_names)
                query += "RETURN r.id"
                result = self.connection_graph.execute(query)
                res = result.column_values('r.id')
                for record in res:
                    result_list.append(int(str(record).replace('"', '')))
        else:
            src, dst = src_dst_label
            for lname in label_name:
                if lname == '':
                    query = f"MATCH (src:{src})-[r]->(dst:{dst}) "
                else:
                    query = f"MATCH (src:{src})-[r:{lname}]->(dst:{dst}) "
                query += self._get_where("r", x_property_names, y_property_names)
                query += "RETURN r.id"
                result = self.connection_graph.execute(query)
                res = result.column_values('r.id')
                for record in res:
                    result_list.append(int(str(record).replace('"', '')))
        return result_list

    def write_property(self, graph_name: str,
                       label_name: str,
                       src_dst_label: (str, str) = None,
                       property_name: str = None,
                       property_values: Dict = None
                       ) -> bool:
        if self.connection_graph == None:
            config = SessionPoolConfig()
            self.connection_graph = SessionPool(self.user_name, self.password, graph_name,
                                                [(self.graph_address.split(":")[0],
                                                  int(self.graph_address.split(":")[1]))])
            assert self.connection_graph.init(config)
        if src_dst_label == None:
            for ID in property_values:
                query = f"UPDATE VERTEX ON {label_name} {ID} SET {property_name} = {property_values[ID]}"
                result = self.connection_graph.execute(query)
                if not result.is_succeeded():
                    query = f"INSERT VERTEX IF NOT EXISTS {label_name} ({property_name}) VALUES {ID}:({property_values[ID]});"
                    result = self.connection_graph.execute(query)
            return True

        else:
            for ID in property_values:
                query = f"UPDATE EDGE ON {label_name} {ID[0]} -> {ID[1]} SET {property_name} = {property_values[ID]}"
                result = self.connection_graph.execute.run(query)
                if not result.is_succeeded():
                    query = f"INSERT EDGE IF NOT EXISTS {label_name}({property_name}) VALUES {ID[0]}->{ID[1]} :({property_values[ID]});"
                    result = self.connection_graph.execute.run(query)
            return True
