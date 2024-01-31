from typing import List, Dict
import torch
import json
from gdbi import NodeExportConfig, EdgeExportConfig, GstoreConnector

class GstoreInterface:
    def GraphDBConnection(self, graph_address:dict, user_name, password):
        if 'IP' not in graph_address or 'Port' not in graph_address or 'httpType' not in graph_address:
            raise ValueError("graph_address 必须包含 'IP', 'Port' 和 'httpType'.")
        self.gc = GstoreConnector.GstoreConnector(graph_address['IP'], graph_address['Port'], user_name, password, http_type=graph_address['httpType'])
        return self.gc
    def get_graph(self, conn: GraphDBConnection,
                  graph_name: str,
                  node_export_config: List[NodeExportConfig],
                  edge_export_config: List[EdgeExportConfig]) -> Dict:
        X_dict = dict()
        edge_index_dict = dict()
        edge_attr_dict = dict()
        Y_dict = dict()
        pos_dict = dict()
        for node_config in node_export_config:
            node_name = node_config.label_name
            query = f"SELECT ?feature_name ?feature_value WHERE {{?node a <{node_name}> . ?node ?feature_name ?feature_value.}}"
            node_result = conn.query(graph_name, "json", query)
            X = list()
            Y = list()
            node_result = json.loads(node_result)
            for record in node_result['results']['bindings']:
                if node_config.x_property_names is not None:
                    if len(node_config.x_property_names) > 0:
                        node_feature = list()
                        for feature_name in node_config.x_property_names:
                            if record["feature_name"]["value"] == feature_name:
                                feature_item = str(record['feature_value']['value']).replace("[", "").replace("]", "").replace(",", " ").split()
                                node_feature.append([float(i) for i in feature_item])
                        # print(node_feature)
                        if node_feature!=[]:
                            X.append(node_feature)
                    # else:
                    #     if record['feature_name']['value'] == node_config.x_property_names[0]:
                    #         feature_item = str(record['feature_value']['value']).replace("[", "").replace("]", "").replace(",", " ").split()
                    #         X.append([float(i) for i in feature_item])
                if node_config.y_property_names is not None:
                    if len(node_config.y_property_names) > 0:
                        label = list()
                        for label_name in node_config.y_property_names:
                            if record['feature_name']['value'] == label_name:
                                label.append(float(record['feature_value']['value']))
                        if label!=[]:
                            Y.append(label)
                    # else:
                    #     # 需要进行判断：record['feature_name']['value'] == node_config.y_property_names[0]
                    #     # 再取值：float(record['feature_value']['value'])
                    #     if record['feature_name']['value'] == node_config.y_property_names[0]:
                    #         Y.append(float(record['feature_value']['value']))
            X_dict.update({node_config.label_name: torch.tensor(X)})
            Y_dict.update({node_config.label_name: torch.tensor(Y)})

        for edge_config in edge_export_config:
            node1_name, node2_name = edge_config.src_dst_label
            edge_name = edge_config.label_name

            query = f"SELECT ?srcID ?dstID ?p WHERE {{?src a <{node1_name}>. ?dst a <{node2_name}>. ?src ?p ?dst. ?src <id> ?srcID. ?dst <id> ?dstID . ?p a <{edge_name}>}}"
            edge_result = conn.query(graph_name, "json", query)
            edge_result = json.loads(edge_result)
            src_node = list()
            dst_node = list()
            edge_attr = list()
            for record in edge_result['results']['bindings']:
                src_node.append(int(record['srcID']['value']))
                dst_node.append(int(record['dstID']['value']))
                edge = record['p']['value']
                if edge_config.x_property_names is not None:
                    query1 = f"SELECT ?property_name ?property_value WHERE {{ <{edge}> ?property_name ?property_value.}}"
                    edge_property_result = conn.query(graph_name, 'json', query1)
                    edge_property_result = json.loads(edge_property_result)
                    for property_record in edge_property_result['results']['bindings']:
                        if len(edge_config.x_property_names) > 0:
                            edge_feature = list()
                            for feature_name in edge_config.x_property_names:
                                if property_record['property_name']['value'] == feature_name:
                                    feature_item = str(property_record['property_value']['value']).replace("[", "").replace("]", "").replace(",", " ").split()
                                    edge_feature.append([float(i) for i in feature_item])
                            edge_attr.append(edge_feature)
                        # else:
                        #     if  property_record['property_name']['value'] == edge_config.x_property_names[0]:
                        #         feature_item = str(property_record['property_value']['value']).replace("[", "").replace("]", "").replace(",", " ").split()
                        #         edge_attr.append([float(i) for i in feature_item])
                            # edge_attr.append([i for i in feature_item])
        edge_index = [src_node, dst_node]
        edge_index_dict.update({edge_config.label_name: torch.tensor(edge_index)})
        # edge_attr_dict.update({edge_config.label_name: torch.tensor(edge_attr)})
        edge_attr_dict.update({edge_config.label_name: edge_attr})


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
        ID_list = []
        if src_dst_label is None:
            for lname in label_name:
                if lname == '':
                    query = f"SELECT ?id WHERE {{?node <id> ?id . "
                else:
                    node_name =lname
                    query = f"SELECT ?id WHERE {{?node a <{node_name}> . ?node <id> ?id ."
                if x_property_names:
                    for x in x_property_names:
                        query +=  f"?node <{x}> {x_property_names[x]}. "
                if y_property_names:
                    for y in y_property_names:
                        query += f"?node <{y}> {y_property_names[y]}. "
                query += f"}}"
                result = self.gc.query(graph_name, "json", query)
                result = json.loads(result)
                values = result['results']['bindings']
                if values != []:
                    for value in values:
                        ID_list.append(value['id']['value'])

            for lname in label_name:
                if lname == '':
                    query = f"SELECT ?srcID ?dstID WHERE {{?src ?edge ?dst. ?src <id> ?srcID. ?dst <id> ?dstID.  "
                else:
                    edge_name = lname
                    query = f"SELECT ?srcID ?dstID WHERE {{?src ?edge ?dst. ?src <id> ?srcID. ?dst <id> ?dstID. ?edge a <{edge_name}> ."
                if x_property_names:
                    for x in x_property_names:
                        query += f"?edge <{x}> {x_property_names[x]}."
                if y_property_names:
                    for y in y_property_names:
                        query += f"?edge <{y}> {y_property_names[y]}. "
                query += f"}}"
                result = self.gc.query(graph_name, "json", query)
                result = json.loads(result)
                values = result['results']['bindings']
                if values!=[]:
                    for value in values:
                        ID_list.append(value['srcID']['value'])
                        ID_list.append(value['dstID']['value'])

        else:
            src, dst = src_dst_label
            for lname in label_name:
                if lname == '':
                    query = f"SELECT ?srcID ?dstID WHERE {{?src a <{src}>. ?dst a <{dst}>. ?src <id> ?srcID. ?dst <id> ?dstID. "
                else:
                    edge_name = lname
                    query = f"SELECT ?srcID ?dstID WHERE {{?src a <{src}>. ?dst a <{dst}>. ?edge a <{edge_name}>. ?src ?edge ?dst. ?src <id> ?srcID. ?dst <id> ?dstID."
                if x_property_names:
                    for x in x_property_names:
                        query += f"?edge <{x}> {x_property_names[x]}. "
                if y_property_names:
                    for y in y_property_names:
                        query += f"?edge <{y}> {y_property_names[y]}. "
                query += f"}}"
                result = self.gc.query(graph_name, "json", query)
                result = json.loads(result)
                values = result['results']['bindings']
                if values != []:
                   for value in values:
                       ID_list.append(value['srcID']['value'])
                       ID_list.append(value['dstID']['value'])
        return ID_list




    def write_property(self, graph_name: str,
                       label_name: str,
                       src_dst_label: (str, str) = None,
                       property_name: str = None,
                       property_values: Dict = None) -> bool:
        if src_dst_label == None:
            for ID in property_values:
                query = f"INSERT {{ ?n <{property_name}> {property_values[ID]}}} WHERE {{?n a <{label_name}>. ?n <id> \"{ID}\"^^<http://www.w3.org/2001/XMLSchema#integer>}}"
                result = self.gc.query(graph_name, "json", query)
                result = json.loads(result)
                if not result['StatusCode']:
                    prefix = str.lower(label_name)
                    query = f"INSERT DATA {{ <{prefix}/{ID}> a <{label_name}>. <{prefix}/{ID}> <id> \"{ID}\"^^<http://www.w3.org/2001/XMLSchema#integer>. <{prefix}/{ID}> <{property_name}> {property_values[ID]}}}"
                    result = self.gc.query(graph_name, "json", query)
            return True
        else:
            for ID in property_values:
                src, dst = src_dst_label
                query = f"INSERT {{?r <{property_name}> {property_values[ID]}}} WHERE {{?src ?r ?dst. ?r a <{label_name}> .  ?src a <{src}>. ?src <id> \"{ID[0]}\"^^<http://www.w3.org/2001/XMLSchema#integer>. ?dst a <{dst}>. ?dst <ID> \"{ID[1]}\"^^<http://www.w3.org/2001/XMLSchema#integer>. }}"
                result = self.gc.query(graph_name, "json", query)
                result = json.loads(result)
                if not result['StatusCode']:
                    prefix = str.lower(label_name)
                    query = f"INSERT {{?src <{prefix}/{ID[0]}/{ID[1]}> ?dst. <{prefix}/{ID[0]}/{ID[1]}> a <{label_name}>. <{prefix}/{ID[0]}/{ID[1]}> <{property_name}> {property_values[ID]} }} WHERE {{ ?src a <{src}>. ?src <id> \"{ID[0]}\"^^<http://www.w3.org/2001/XMLSchema#integer>. ?dst a <{dst}>. ?dst <id> \"{ID[1]}\"^^<http://www.w3.org/2001/XMLSchema#integer>.}}"
                    result = self.gc.query(graph_name, "json", query)
            return True




# if __name__ == "__main__":
#     graph_address = {'IP':'61.136.101.220', 'Port':'20022','httpType':'ghttp'}
#     user_name = "root"
#     password = "123456"
#     db_name = "cora"
#     gstore_instance = gstoreInstance()
#     cnn = gstore_instance.GraphDBConnection(graph_address,user_name,password)
# # get_graph
#     node1 = NodeExportConfig('Paper',['feature'],['classLabel'])
#     edge1 = EdgeExportConfig('Cite', ('Paper','Paper'),[],[])
#     graph = gstore_instance.get_graph(cnn, db_name,[node1], [edge1])
#     print(graph)
#     import pickle
#     with open("cora_graph.pkl", 'wb') as file:
#         pickle.dump(graph, file)
    # with open('cora_graph.pkl', 'rb') as f:
    #     data = pickle.load(f)
    #     print(data)
## match
    # label_name1 = ['Paper']
    # x_property_names1 = {'classLabel': '"0"^^<http://www.w3.org/2001/XMLSchema#integer>'}
    # x_property_names2 = {'classLabel': '"1"^^<http://www.w3.org/2001/XMLSchema#integer>'}
    # y_property_names2 = {'paperId':'48766'}
    # label_name3 = ['Cite']
    # src_dst_label3 = ('Paper', 'Paper')
    # id_list1 = gstore_instance.match(graph_name=db_name,label_name=label_name1,x_property_names=x_property_names1)
    # print(id_list1)
    # print(len(id_list1))
    # id_list2 = gstore_instance.match(graph_name=db_name,label_name=label_name1,x_property_names=x_property_names2,y_property_names=y_property_names2)
    # print(id_list2)
    # print(len(id_list2))

## write_property
    # label_name1 = 'Paper'
    # property_name1 = 'gcn'
    # property_values1 = {0: '0.3939307,0.4749441,0.6870685,-0.8042017,0.82710814,0.7153123,-0.49821174',
    #                   3000: '-0.5643787,0.47391596,0.2563388,-0.26626328,-0.46077794,-0.8464279,0.6493137'}
    # label_name2 = 'Cite'
    # property_name2 = 'edgeLabel'
    # src_dst_label2 = ('Paper', 'Paper')
    # property_values2 = {(837,1686):'"0"^^<http://www.w3.org/2001/XMLSchema#integer>', (0,3000):'"1"^^<http://www.w3.org/2001/XMLSchema#integer>'}
    # print(gstore_instance.write_property(graph_name=db_name, label_name=label_name1, property_name=property_name1, property_values=property_values1))
    # print(gstore_instance.write_property(graph_name=db_name,label_name=label_name2,src_dst_label=src_dst_label2,property_name=property_name2,property_values=property_values2))