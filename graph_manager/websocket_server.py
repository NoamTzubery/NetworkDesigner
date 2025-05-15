# server.py
import asyncio
import json
import websockets
import networkx as nx
from networkx.readwrite import json_graph
from graph_manager.graph_creation import GraphManager
from database_manager.mongo_handler import Database


async def handler(websocket, path):
    print("Client connected.")

    try:
        # Step 1: Receive authentication or signup request
        auth_request = await websocket.recv()
        auth_data = json.loads(auth_request)

        action = auth_data.get("action")  # "signup" or "login"
        username = auth_data.get("username")
        password = auth_data.get("password")

        if not action or not username or not password:
            await websocket.send(json.dumps({"error": "Missing action, username, or password."}))
            return

        # Step 2: Handle sign-up
        if action == "signup":
            result = Database.create_user(username, password)
            if "error" in result:
                await websocket.send(json.dumps({"error": result["error"]}))
                return
            await websocket.send(json.dumps({
                "message": result["message"],
                "user_id": result["user_id"]
            }))
            print(f"New user registered: {username}")
            return

        # Step 3: Handle login
        elif action == "login":
            user = Database.authenticate_user(username, password)
            if not user:
                await websocket.send(json.dumps({"error": "Authentication failed"}))
                return
            print(f"User {username} authenticated with role: {user['role']}")
        else:
            await websocket.send(json.dumps({"error": "Invalid action. Must be 'login' or 'signup'."}))
            return

        # Step 4: Enter a loop to handle multiple requests after login
        while True:
            try:
                request = await websocket.recv()
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed by the client.")
                break

            print("Received request from client:", request)
            data = json.loads(request)
            req_action = data.get("action", "")

            if req_action == "create_graph":
                # Extract graph configuration parameters
                num_routers = data.get("num_routers", 2)
                num_mls = data.get("num_mls", 2)
                num_switches = data.get("num_switches", 4)
                num_computers = data.get("num_computers", 15)
                mode = data.get("mode", 1)
                ip_base = data.get("ip_base", "192.168.0.0")

                # ── NEW: pull topology_name & vlan_count from client
                topology_name = data.get("topology_name", "Untitled Topology")
                vlan_count    = data.get("vlan_count", -1)

                # Instantiate GraphManager with VLAN count
                graph_manager = GraphManager(
                    num_routers,
                    num_mls,
                    num_switches,
                    num_computers,
                    mode,
                    ip_base,
                    vlan_count
                )

                access_graph_data = json_graph.node_link_data(graph_manager.access_graph)
                top_graph_data = json_graph.node_link_data(graph_manager.top_graph)
                access_configuration = graph_manager.access_device_config
                top_layer_configurations = graph_manager.top_device_config

                graph_id = Database.save_graph(
                    user["user_id"],
                    access_graph_data,
                    top_graph_data,
                    access_configuration,
                    top_layer_configurations,
                    topology_name,
                    vlan_count
                )

                # ── NEW: include them in the reply
                message = {
                    "message": "Graph created and saved.",
                    "graph_id": graph_id,
                    "topology_name": topology_name,
                    "vlan_count": vlan_count,
                    "access_graph": access_graph_data,
                    "top_graph": top_graph_data,
                    "access_configuration": access_configuration,
                    "top_layer_configurations": top_layer_configurations
                }

                await websocket.send(json.dumps(message))
                print("Graph creation data and configurations sent to client.")

            elif req_action == "get_history":
                user_graphs = Database.get_user_graphs(user["user_id"])
                response = {"graphs": user_graphs}
                await websocket.send(json.dumps(response))
                print("Sent topology history to client.")

            else:
                await websocket.send(json.dumps({"error": "Unknown action."}))
                print("Unknown action received from client.")

    except Exception as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        await websocket.send(json.dumps({"error": error_msg}))


async def main():
    async with websockets.serve(handler, "localhost", 6789):
        print("WebSocket server started on ws://localhost:6789")
        await asyncio.Future()  # Keep the server running


if __name__ == "__main__":
    asyncio.run(main())
