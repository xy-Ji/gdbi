from neo4j import GraphDatabase
from gammagl.data.feature_store import FeatureStore, TensorAttr
import tensorlayerx as tlx

class Neo4jFeatureStore(FeatureStore):
    def __init__(self, uri: str, user_name: str, password: str, **kwargs):
        super().__init__()
        self.driver = GraphDatabase.driver(uri, auth=(user_name, password))

    def __del__(self):
        self.driver.close()

    def _put_tensor(self, tensor, attr: TensorAttr):
        with self.driver.session() as session:
            group_name = attr.group_name
            attr_name = attr.attr_name
            index = attr.index
            
            for i in range(len(tensor)):
                query = f"MATCH (n:{group_name} {{ID:{index[i]}}} ) SET n.{attr_name} = '{tlx.convert_to_numpy(tensor[i])}';"
                result = session.run(query)
                if not result.consume().counters._contains_updates:
                    query = f"CREATE (n:{group_name} {{ID: {index[i]}, {attr_name}: '{tlx.convert_to_numpy(tensor[i])}'}});"
                    session.run(query)
        return True

    def _get_tensor(self, attr: TensorAttr):
        with self.driver.session() as session:
            group_name = attr.group_name
            attr_name = attr.attr_name
            index = attr.index
            
            data = []
            for id in index:
                query = f"MATCH (n:{group_name} {{ID:{id}}} ) RETURN n.{attr_name} AS value;"
                result = session.run(query)
                for record in result:
                    if record['value'] is None:
                        continue
                    value = record['value'].replace("[", "").replace("]", "").replace(",", " ").split()
                    data.append([float(i) for i in value])
        return tlx.convert_to_tensor(data)

    def _remove_tensor(self, attr):
        with self.driver.session() as session:
            group_name = attr.group_name
            attr_name = attr.attr_name
            index = attr.index
            
            for id in index:
                query = f"MATCH (n:{group_name} {{ID:{id}}} ) REMOVE n.{attr_name};"
                session.run(query)
        return True

    def _get_tensor_size(self, attr):
        tensor = self._get_tensor(attr)
        return tensor.shape

    def get_all_tensor_attrs(self):
        with self.driver.session() as session:
            result_list = []
            label = session.run("CALL db.labels() YIELD label RETURN DISTINCT label;")
            for record in label:
                group_name = record['label']
                query = f"MATCH (n:{group_name}) RETURN DISTINCT keys(n) AS properties;"
                properties = session.run(query)
                attr_names = set()
                for prop in properties:
                    for attr_name in prop['properties']:
                        if attr_name not in attr_names:
                            attr_names.add(attr_name)
                for attr_name in attr_names:
                    result_list.append(TensorAttr(group_name, attr_name))
        return result_list