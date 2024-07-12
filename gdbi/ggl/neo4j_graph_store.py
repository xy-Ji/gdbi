from neo4j import GraphDatabase
from gammagl.data.graph_store import EdgeAttr, EdgeLayout, GraphStore, EdgeTensorType
from typing import List
import tensorlayerx as tlx

class Neo4jGraphStore(GraphStore):
    def __init__(self, uri: str, user_name: str, password: str, **kwargs):
        super().__init__()
        self.driver = GraphDatabase.driver(uri, auth=(user_name, password))
    
    def __del__(self):
        self.driver.close()
    
    def _put_edge_index(self, edge_index, edge_attr: EdgeAttr) -> bool:
        batch_size = 128
        with self.driver.session() as session:
            for i in range(0, edge_index[0].size(0), batch_size):
                batch_queries = []
                for j in range(i, min(i + batch_size, edge_index[0].size(0))):
                    batch_queries.append({
                        "src_id": edge_index[0][j].item(),
                        "dst_id": edge_index[1][j].item()
                    })

                session.run(
                    """
                    UNWIND $rels AS rel
                    MERGE (n {ID: rel.src_id}) 
                    MERGE (m {ID: rel.dst_id}) 
                    """ + f"MERGE (n)-[r:{edge_attr.edge_type}]->(m)",
                    rels=batch_queries
                )
        return True
    
    def _get_edge_index(self, edge_attr: EdgeAttr) -> EdgeTensorType:
        with self.driver.session() as session:
            result = session.run(
                f"MATCH (n)-[r:{edge_attr.edge_type}]->(m) RETURN n.ID AS src_id, m.ID AS dst_id",
            )
            src_ids = []
            dst_ids = []
            for record in result:
                src_ids.append(int(record['src_id']))
                dst_ids.append(int(record['dst_id']))
            edge_index = tlx.convert_to_tensor([src_ids,dst_ids])
        return edge_index
    
    def _remove_edge_index(self, edge_attr: EdgeAttr) -> bool:
        with self.driver.session() as session:
            session.run(f"MATCH (n)-[r:{edge_attr.edge_type}]->(m) DELETE r")
        return True
    
    def get_all_edge_attrs(self) -> List[EdgeAttr]:
        with self.driver.session() as session:
            result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
        return [EdgeAttr(record['relationshipType'], EdgeLayout.COO) for record in result]