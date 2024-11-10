import networkx as nx
import matplotlib.pyplot as plt
import math


class GraphManager:
    def __init__(self, num_routers, num_switches, num_computers):
        self.num_routers = num_routers
        self.num_switches = num_switches
        self.num_computers = num_computers
        self.graph = self.create_optimized_topology()

    def create_optimized_topology(self):
        G = nx.Graph()

        # Add routers, switches, and computers to the graph
        routers = [f'Router_{i}' for i in range(self.num_routers)]
        switches = [f'Switch_{i}' for i in range(self.num_switches)]
        computers = [f'Computer_{i}' for i in range(self.num_computers)]

        G.add_nodes_from(routers)
        G.add_nodes_from(switches)
        G.add_nodes_from(computers)

        return G

