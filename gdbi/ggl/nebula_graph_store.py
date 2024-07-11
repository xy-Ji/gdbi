from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config
from gammagl.data.graph_store import EdgeAttr, EdgeLayout, GraphStore, EdgeTensorType
from typing import List
import tensorlayerx as tlx

class NebulaGraphStore(GraphStore):
    def __init__(self, ip: str, port: int, user_name: str, password: str, graph_name: str, **kwargs):
        super().__init__()
        config = Config()
        config.max_connection_pool_size = 100
        
        connection_pool = ConnectionPool()
        connection_pool.init([(ip, port)], config)
        self.conn = connection_pool
        
        self.user_name = user_name
        self.password = password
        self.graph_name = graph_name
    
        self.create_space()

    def __del__(self):
        self.conn.close()
    
    def create_space(self):
        session = self.conn.get_session(self.user_name, self.password)
        session.execute(f'CREATE SPACE IF NOT EXISTS {self.graph_name} (vid_type=INT64)')
        session.release()
    
    def _put_edge_index(self, edge_index, edge_attr: EdgeAttr) -> bool:
        session = self.conn.get_session(self.user_name, self.password)
        session.execute(f"USE {self.graph_name};")
        
        session.execute(f"CREATE EDGE IF NOT EXISTS {edge_attr.edge_type};")

        for i in range(len(edge_index[0])):
            session.execute(
                f"INSERT EDGE {edge_attr.edge_type} VALUES {edge_index[0][i].item()} -> {edge_index[1][i].item()}:();"
            )
        
        session.release()
        return True
    
    def _get_edge_index(self, edge_attr: EdgeAttr) -> EdgeTensorType:
        session = self.conn.get_session(self.user_name, self.password)
        session.execute(f"USE {self.graph_name};")
        
        result = session.execute(
            f"iMATCH ()-[r:{edge_attr.edge_type}]->() RETURN src(r) AS src_id, dst(r) AS dst_d",
        )
        src_ids = list(map(int, map(str, result.column_values('src_id'))))
        dst_ids = list(map(int, map(str, result.column_values('dst_id'))))
        edge_index = tlx.convert_to_tensor([src_ids,dst_ids])
        
        session.release()
        return edge_index
    
    def _remove_edge_index(self, edge_attr: EdgeAttr) -> bool:        
        edge_index = self._get_edge_index(edge_attr)
        session = self.conn.get_session(self.user_name, self.password)
        session.execute(f"USE {self.graph_name};")
        
        for i in range(len(edge_index[0])):
            session.execute(
                f"DELETE edge {edge_attr.edge_type} {edge_index[0][i]} -> {edge_index[1][i]};"
            )
            
        session.release()
        return True
    
    def get_all_edge_attrs(self) -> List[EdgeAttr]:
        session = self.conn.get_session(self.user_name, self.password)
        session.execute(f"USE {self.graph_name};")

        result = session.execute("MATCH ()-[e]->() RETURN DISTINCT type(e) AS edge_type;")
        edge_types = result.column_values('edge_type')
        return [EdgeAttr(edge_type, EdgeLayout.COO) for edge_type in edge_types]