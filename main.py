import asyncio
import websockets
import json
import networkx as nx
from networkx.readwrite import json_graph
from communication_manager.server import Server
from graph_manager.graph_creation import GraphManager


async def handle_client(websocket, _):
    try:
        # Receive configuration from the client
        config_data = await websocket.recv()
        config = json.loads(config_data)

        # Create the graph based on the configuration
        num_routers = config["num_routers"]
        num_switches = config["num_distribution_switches"] + config["num_access_switches"]
        num_computers = config["num_devices"]

        graph_manager = GraphManager(num_routers, num_switches, num_computers)
        graph = graph_manager.graph

        # Convert the graph to JSON and send it to the client
        json_graph_data = json_graph.node_link_data(graph)
        await websocket.send(json.dumps(json_graph_data))
        print("Topology graph sent to client.")

    except websockets.ConnectionClosed:
        print("Connection closed by client.")


async def main():
    server = await websockets.serve(handle_client, "localhost", 6789)
    print("Server started on ws://localhost:6789")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
