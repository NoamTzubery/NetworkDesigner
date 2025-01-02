import networkx as nx
import matplotlib.pyplot as plt
import math


class Device:
    def __init__(self, name, device_type, routing=False):
        """
        device_type: "Router", "MultiLayerSwitch", "Switch", "Computer"
        routing: Boolean indicating if device has routing capability
        """
        self.name = name
        self.device_type = device_type
        self.routing = routing


class GraphManager:
    def __init__(self, num_routers, num_mls, num_switches, num_computers):
        """
        :param num_routers: Number of routers
        :param num_mls: Number of multilayer (L3) switches
        :param num_switches: Number of regular L2 switches
        :param num_computers: Number of computers
        """

        self.num_routers = num_routers
        self.num_mls = num_mls
        self.num_switches = num_switches
        self.num_computers = num_computers

        # Naming each device
        self.routers = [Device(f'Router_{i + 1}', "Router", routing=True) for i in range(num_routers)]
        self.mls = [Device(f'MultiLayerSwitch_{i + 1}', "MultiLayerSwitch", routing=True) for i in range(num_mls)]
        self.switches = [Device(f'Switch_{i + 1}', "Switch", routing=False) for i in range(num_switches)]
        self.computers = [Device(f'Computer_{i + 1}', "Computer", routing=False) for i in range(num_computers)]

        self.graph = self.create_optimized_topology()

        # Attempt to create the topology
        if not self.assign_devices_to_layers():
            print("We cannot create a valid 3-tier network with the given devices.")
        else:
            # Only add nodes/edges if successful
            self.create_optimized_topology()

    def assign_devices_to_layers(self):

        layers = {
            "Core": [],
            "Distribution": [],
            "Access": []
        }

        # Assign Routers to Core Layer
        if self.num_routers > 1:  # Enough routers for a core layer
            layers["Core"].extend(self.routers)
            core_used = self.num_routers
        else:
            core_used = 0  # No core layer, assign routers elsewhere

        # Assign Switches to Distribution and Access Layers
        if core_used > 0:  # If we have a core layer
            dist_switches = max(1, self.num_switches // 2)  # Assign enough switches for distribution
            layers["Distribution"].extend(self.switches[:dist_switches])
            layers["Access"].extend(self.switches[dist_switches:])
        else:  # Merge core and distribution layers
            dist_switches = max(1, (self.num_switches + core_used) // 2)
            layers["Distribution"].extend(self.routers + self.switches[:dist_switches])
            layers["Access"].extend(self.switches[dist_switches:])

        # Assign Computers to Access Layer
        layers["Access"].extend(self.computers)

        return layers

    def create_topology_for_access_layer(self):
        return

    def create_optimized_topology(self):
        G = nx.Graph()

        # Add routers, switches, and computers to the graph
        G.add_nodes_from(self.routers)
        G.add_nodes_from(self.switches)
        G.add_nodes_from(self.computers)

        # Assign devices to layers
        layers = self.assign_devices_to_layers()

        # Create connections between layers
        # Connect Core to Distribution
        for router in layers["Core"]:
            for switch in layers["Distribution"]:
                G.add_edge(router, switch)

        # Connect Distribution to Access
        for switch in layers["Distribution"]:
            for access_device in layers["Access"]:
                G.add_edge(switch, access_device)

        return G

    def draw_topology(self):
        pos = nx.spring_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True, node_size=2000, node_color="skyblue", font_size=10,
                font_weight="bold")
        plt.show()
