import networkx as nx
from access_layer import create_optimal_vlan_network, visualize_graph
from access_configuration import configure_devices, display_device_configurations

MINIMUM_ROUTING = 3
SWITCHES_MINIMUM_MULTIPLIER = 7


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
    def __init__(self, num_routers, num_mls, num_switches, num_computers, mode=1):
        """
        :param num_routers: Number of routers
        :param num_mls: Number of multilayer (L3) switches
        :param num_switches: Number of regular L2 switches
        :param num_computers: Number of computers
        :param mode: Network mode (0: fault-tolerant, 1: scalable)
        """
        print(f"Initializing GraphManager with:\n"
              f"Routers: {num_routers}, MLS: {num_mls}, Switches: {num_switches}, Computers: {num_computers}, Mode: {mode}")

        self.num_routers = num_routers
        self.num_mls = num_mls
        self.num_switches = num_switches
        self.num_computers = num_computers
        self.mode = mode

        # Naming devices
        self.routers = [Device(f'Router_{i + 1}', "Router", routing=True) for i in range(num_routers)]
        self.mls = [Device(f'MultiLayerSwitch_{i + 1}', "MultiLayerSwitch", routing=True) for i in range(num_mls)]
        self.switches = [Device(f'Switch_{i + 1}', "Switch", routing=False) for i in range(num_switches)]
        self.computers = [Device(f'Computer_{i + 1}', "Computer", routing=False) for i in range(num_computers)]

        print(f"Devices initialized:\n"
              f"Routers: {[router.name for router in self.routers]}\n"
              f"MLS: {[mls.name for mls in self.mls]}\n"
              f"Switches: {[switch.name for switch in self.switches]}\n"
              f"Computers: {[computer.name for computer in self.computers]}")

        # Create layers
        self.layers = self.assign_devices_to_layers()
        print("Devices assigned to layers:", self.layers)

        # Create the topology
        self.graph = self.create_optimized_topology()

    def assign_devices_to_layers(self):
        """
        Assign devices to Core, Distribution, and Access layers.
        Returns a dictionary with devices grouped by layer.
        """
        print("Assigning devices to layers...")
        layers = {
            "Core": [],
            "Distribution": [],
            "Access": []
        }

        #if self.num_switches * SWITCHES_MINIMUM_MULTIPLIER < self.num_computers:
        #    print("Insufficient computers to meet the switch multiplier requirement.")
        #    return 0

        # Assign Routers to Core Layer
        if self.num_routers + self.num_mls >= MINIMUM_ROUTING:  # Enough routers for a core layer
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

        print(f"Layer assignments:\nCore: {[device.name for device in layers['Core']]}\n"
              f"Distribution: {[device.name for device in layers['Distribution']]}\n"
              f"Access: {[device.name for device in layers['Access']]}")
        return layers

    def create_optimized_topology(self):
        """
        Create a complete topology by integrating access, distribution, and core layers.
        """
        print("Creating optimized topology...")
        G = nx.Graph()

        # Access Layer: Create VLAN-based network
        vlan_devices = [device.name for device in self.layers["Access"]]
        switches = [device for device in vlan_devices if "Switch" in device]
        computers = [device for device in vlan_devices if "Computer" in device]

        print(f"Access layer devices:\nSwitches: {switches}\nComputers: {computers}")
        vlan_graph, vlans = create_optimal_vlan_network(len(switches), len(computers), self.mode)
        G = nx.compose(G, vlan_graph)

        # Configure Access Layer Devices
        ip_base = "192.168.0.0"
        device_configurations = configure_devices(vlans, ip_base)

        # Display configurations
        print("\nDevice Configurations for Access Layer:")
        display_device_configurations(device_configurations)

        # Future: Add Core and Distribution Layers
        print("Topology created with access layer (core/distribution layers are placeholders).")
        return G

    def draw_topology(self):
        """
        Visualize the created network topology.
        """
        print("Visualizing the network topology...")
        visualize_graph(self.graph, "Three-Tier Network Topology")


# Example usage
if __name__ == "__main__":

    num_routers = 2
    num_mls = 2
    num_switches = 5
    num_computers = 15
    mode = 1  # 0 for fault-tolerant, 1 for scalable

    print("Starting GraphManager...")
    graph_manager = GraphManager(num_routers, num_mls, num_switches, num_computers, mode)
    graph_manager.draw_topology()
    print("GraphManager finished execution.")
