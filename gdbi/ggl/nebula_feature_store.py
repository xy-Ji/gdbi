from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config
from gammagl.data.feature_store import FeatureStore, TensorAttr
import tensorlayerx as tlx

class NebulaFeatureStore(FeatureStore):
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

    def __del__(self):
        self.conn.close()

    def _put_tensor(self, tensor, attr: TensorAttr):
        session = self.conn.get_session(self.user_name, self.password)
        session.execute(f"USE {self.graph_name};")
        
        group_name = attr.group_name
        attr_name = attr.attr_name
        index = attr.index
        
        session.execute(f"CREATE TAG IF NOT EXISTS {group_name}({attr_name} string);")
        session.execute(f"ALTER TAG {group_name} ADD ({attr_name} string);")
        for i in range(len(tensor)):
            query = f"INSERT VERTEX {group_name}({attr_name}) VALUES {index[i]}:('{tlx.convert_to_numpy(tensor[i])}');"
            session.execute(query)
        
        session.release()
        return True

    def _get_tensor(self, attr: TensorAttr):
        session = self.conn.get_session(self.user_name, self.password)
        session.execute(f"USE {self.graph_name};")
        
        group_name = attr.group_name
        attr_name = attr.attr_name
        index = attr.index
        
        data = []
        for id in index:
            query = f"FETCH PROP ON {group_name} {id} YIELD {group_name}.{attr_name} AS value;"
            result = session.execute(query).column_values("value")
            for record in result:
                value = str(record).replace("[", "").replace("]", "").replace(",", " ").replace('"', '').split()
                data.append([float(i) for i in value])
        
        session.release()
        return tlx.convert_to_tensor(data)

    def _remove_tensor(self, attr):
        session = self.conn.get_session(self.user_name, self.password)
        session.execute(f"USE {self.graph_name};")
        
        group_name = attr.group_name
        attr_name = attr.attr_name
        index = attr.index
        
        for id in index:
            query = f"UPDATE VERTEX ON {group_name} {id} SET {attr_name} = '';"
            session.execute(query)
        return True

    def _get_tensor_size(self, attr):
        tensor = self._get_tensor(attr)
        return tensor.shape

    def get_all_tensor_attrs(self):
        session = self.conn.get_session(self.user_name, self.password)
        session.execute(f"USE {self.graph_name};")

        result_list = []
        label = session.execute("SHOW TAGS;")       
        for record in label:
            group_name = str(record).replace('"', '')
            query = f"DESCRIBE TAG {group_name};"
            result = session.execute(query)
            properties = result.column_values('Field')
            for prop in properties:
                result_list.append(TensorAttr(group_name, prop))
                
        session.release()
        return result_list