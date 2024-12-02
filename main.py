import asyncio
import websockets
import json
import networkx as nx
from networkx.readwrite import json_graph
from communication_manager.server import Server
from graph_manager.graph_creation import GraphManager
import configparser


def get_server_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    host = config["server"]["host"]
    port = int(config["server"]["port"])
    return host, port


async def handle_client(websocket, _):
    try:
        # Receive configuration from the client
        config_data = await websocket.recv()
        config = json.loads(config_data)

        # Create the graph based on the configuration
        num_routers = config["num_routers"]
        num_switches = config["num_distribution_switches"]
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
    # Get server configuration
    host, port = get_server_config("config.ini")

    # Start the WebSocket server
    server = await websockets.serve(handle_client, host, port)
    print(f"Server started on ws://{host}:{port}")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
