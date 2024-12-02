import asyncio
import websockets
import json
from networkx.readwrite import json_graph


class Server:
    def __init__(self, graph, host, port):
        self.graph = graph
        self.host = host
        self.port = port

    async def send_graph(self, websocket, _):
        data = json_graph.node_link_data(self.graph)
        json_data = json.dumps(data)
        await websocket.send(json_data)
        print("Graph sent to client.")

    async def start_server(self):
        server = await websockets.serve(self.send_graph, self.host, self.port)
        print(f"Server started on ws://{self.host}:{self.port}")
        await server.wait_closed()
