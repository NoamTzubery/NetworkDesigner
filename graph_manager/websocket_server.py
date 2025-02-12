import asyncio
import json
import websockets
import networkx as nx
from networkx.readwrite import json_graph

from graph_manager.graph_creation import GraphManager


async def handler(websocket, path):
    print("Client connected.")
    try:
        # Wait for a message from the client containing configuration data.
        request = await websocket.recv()
        print("Received request from client:", request)
        data = json.loads(request)
        num_routers = data.get('num_routers', 2)
        num_mls = data.get('num_mls', 2)
        num_switches = data.get('num_switches', 4)
        num_computers = data.get('num_computers', 15)
        mode = data.get('mode', 1)

        # Instantiate your GraphManager with the received parameters.
        graph_manager = GraphManager(num_routers, num_mls, num_switches, num_computers, mode)

        # Serialize the networkx graphs into a JSON-friendly format.
        access_graph_data = json_graph.node_link_data(graph_manager.access_graph)
        top_graph_data = json_graph.node_link_data(graph_manager.top_graph)

        # If you had configuration data stored or computed, include it here.
        # (In your current GraphManager, configurations are printed rather than stored.)
        device_configurations = []  # Replace with actual configuration data if available.

        # Prepare a message dictionary.
        message = {
            'access_graph': access_graph_data,
            'top_graph': top_graph_data,
            'device_configurations': device_configurations
        }

        # Send the data back to the client as JSON.
        await websocket.send(json.dumps(message))
        print("Data sent to client.")
    except Exception as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        await websocket.send(json.dumps({"error": error_msg}))


async def main():
    # Start the WebSocket server on localhost at port 6789.
    async with websockets.serve(handler, "localhost", 6789):
        print("WebSocket server started on ws://localhost:6789")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
