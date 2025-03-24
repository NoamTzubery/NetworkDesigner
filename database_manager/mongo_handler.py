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
        """
        if users_collection.find_one({"username": username}):
            return {"error": "Username already exists."}

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_id = str(uuid.uuid4())  # Unique ID for the user

        user_data = {
            "_id": user_id,
            "username": username,
            "password": hashed_pw,
            "role": role
        }
        users_collection.insert_one(user_data)
        return {"message": "User created successfully.", "user_id": user_id}

    @staticmethod
    def authenticate_user(username, password):
        """
        Authenticate user and return user details if successful.
        """
        user = users_collection.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
            return {"user_id": user["_id"], "username": user["username"], "role": user["role"]}
        return None

    @staticmethod
    def save_graph(user_id, access_graph, top_graph):
        """
        Save the generated graph in the database linked to a user.
        """
        graph_data = {
            "user_id": user_id,
            "access_graph": access_graph,
            "top_graph": top_graph
        }
        result = graphs_collection.insert_one(graph_data)
        return str(result.inserted_id)

    @staticmethod
    def get_user_graphs(user_id):
        """
        Retrieve all graphs created by a specific user.
        """
        graphs = graphs_collection.find({"user_id": user_id})
        return [{"_id": str(graph["_id"]), "access_graph": graph["access_graph"], "top_graph": graph["top_graph"]} for graph in graphs]
