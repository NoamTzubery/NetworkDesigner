import pymongo
import bcrypt
import uuid
from pymongo import MongoClient
from bson.objectid import ObjectId

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["network_topology"]
users_collection = db["users"]
graphs_collection = db["graphs"]


class Database:
    @staticmethod
    def create_user(username, password, role="user"):
        """
        Create a new user with a hashed password.
        Returns a dict with either "error" or "message" and "user_id".
        """
        if users_collection.find_one({"username": username}):
            return {"error": "Username already exists."}

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user_id = str(uuid.uuid4())

        user_data = {
            "_id": user_id,
            "username": username,
            "password": hashed_pw,
            "role": role.lower()
        }
        users_collection.insert_one(user_data)
        return {"message": "User created successfully.", "user_id": user_id}

    @staticmethod
    def authenticate_user(username, password):
        """
        Authenticate user. Returns dict with user_id, username, role on success, or None on failure.
        """
        user = users_collection.find_one({"username": username})
        if not user:
            return None

        if bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            return {
                "user_id": user["_id"],
                "username": user["username"],
                "role": user.get("role", "user")
            }
        return None

    @staticmethod
    def save_graph(user_id, access_graph, top_graph,
                   access_configuration=None, top_layer_configurations=None):
        """
        Save a new network topology for the given user, including
        both access-layer and top-layer configurations.
        Returns the string ID of the inserted document.
        """
        graph_data = {
            "user_id": user_id,
            "access_graph": access_graph,
            "top_graph": top_graph,
            "access_configuration": access_configuration or [],
            "top_layer_configurations": top_layer_configurations or []
        }
        result = graphs_collection.insert_one(graph_data)
        return str(result.inserted_id)

    @staticmethod
    def get_user_graphs(user_id):
        """
        Fetch saved topologies for a given user.
        Admins get all; regular users only their own.
        Returns a list of dicts with the graph details and configs.
        """
        user = users_collection.find_one({"_id": user_id})
        if not user:
            return {"error": "User not found."}

        role = user.get("role", "user").lower()
        if role == "admin":
            cursor = graphs_collection.find().sort("_id", pymongo.DESCENDING)
        else:
            cursor = graphs_collection.find(
                {"user_id": user_id}
            ).sort("_id", pymongo.DESCENDING)

        user_graphs = []
        for doc in cursor:
            user_graphs.append({
                "id": str(doc["_id"]),
                "access_graph": doc.get("access_graph"),
                "top_graph": doc.get("top_graph"),
                "access_configuration": doc.get("access_configuration", []),
                "top_layer_configurations": doc.get("top_layer_configurations", [])
            })
        return user_graphs
