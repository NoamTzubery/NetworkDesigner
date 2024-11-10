from pymongo import MongoClient
import networkx as nx
import pickle


class MongoHandler:
    def __init__(self, uri="mongodb://localhost:27017", db_name="network_db", collection_name="topologies"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save_topology(self, name, graph):
        # Serialize the NetworkX graph to a binary format
        graph_data = pickle.dumps(graph)
        # Store the graph with the given name
        self.collection.update_one(
            {"name": name},
            {"$set": {"name": name, "graph": graph_data}},
            upsert=True
        )
        print(f"Topology '{name}' saved successfully.")

    def load_topology(self, name):
        # Retrieve the graph data by name
        result = self.collection.find_one({"name": name})
        if result:
            graph_data = result["graph"]
            # Deserialize the binary data back into a NetworkX graph
            graph = pickle.loads(graph_data)
            print(f"Topology '{name}' loaded successfully.")
            return graph
        else:
            print(f"Topology '{name}' not found in the database.")
            return None

    def close_connection(self):
        self.client.close()
