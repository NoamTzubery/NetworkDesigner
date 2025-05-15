import networkx as nx
from access_layer import create_optimal_vlan_network, visualize_graph
from access_configuration import configure_devices, display_device_configurations
from top_layers import build_topology
from top_layers_configuration import configure_top_layers

MINIMUM_ROUTING = 4
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
    def __init__(self, num_routers, num_mls, num_switches, num_computers, mode=1, ip_base="192.168.0.0", vlan_count=-1):
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
        self.ip_base = ip_base
        self.mode = mode
        self.vlan_count = vlan_count

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
        (self.access_graph, self.top_graph, self.access_device_config,
         self.top_device_config) = self.create_optimized_topology()

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

        # Combine and prioritize routing devices
        routing_devices = sorted(self.routers + self.mls, key=lambda d: d.device_type == "Router", reverse=True)

        # Check if there are enough routing devices for a three-tier topology
        if len(routing_devices) < MINIMUM_ROUTING:
            print("Not enough routing devices for a three-tier topology. Collapsing to two-tier topology.")
            layers["Distribution"] = routing_devices  # All routing devices form the top layer
            layers["Access"].extend(self.switches + self.computers)  # Non-routing devices form the bottom layer
            return layers

        # Assign Multi-Layer Switches to Core Layer first
        core_devices = min(len(routing_devices), 2)  # At least two devices in Core
        layers["Core"] = routing_devices[:core_devices]

        # Remaining routing devices go to the Distribution Layer
        layers["Distribution"] = routing_devices[core_devices:]

        # Non-routing devices go to the Access Layer
        layers["Access"].extend(self.switches + self.computers)

        print(f"Layer assignments:\nCore: {[device.name for device in layers['Core']]}\n"
              f"Distribution: {[device.name for device in layers['Distribution']]}\n"
              f"Access: {[device.name for device in layers['Access']]}")
        return layers

    def create_optimized_topology(self):
        """
        Create a complete topology by integrating access, distribution, and core layers.
        """
        print("Creating optimized topology...")
        access_graph = nx.Graph()
        top_graph = nx.Graph()

        # Access Layer: Create VLAN-based network
        vlan_devices = [device.name for device in self.layers["Access"]]
        switches = [device for device in vlan_devices if "Switch" in device]
        computers = [device for device in vlan_devices if "Computer" in device]

        print(f"Access layer devices:\nSwitches: {switches}\nComputers: {computers}")
        vlan_graph, vlans = create_optimal_vlan_network(len(switches), len(computers), self.mode, self.vlan_count)
        access_graph = nx.compose(access_graph, vlan_graph)

        # Configure Access Layer Devices

        device_configurations, main_access_switches, next_ip = configure_devices(vlans, self.ip_base)
        top_graph = build_topology(
            [device.name for device in self.layers["Distribution"]],
            [device.name for device in self.layers["Core"]],
            main_access_switches
        )

        top_layer_configurations = configure_top_layers(
            [device.name for device in self.layers["Distribution"]],
            [device.name for device in self.layers["Core"]],
            main_access_switches,
            next_ip
        )

        # Display configurations
        print("\nDevice Configurations for Access Layer:")
        display_device_configurations(device_configurations)
        print(main_access_switches)

        # Extract only main access switch configurations
        main_switch_configurations = [config for config in device_configurations if config["name"] in
                                      main_access_switches]

        # Print or return main_switch_configurations as needed
        print("\nMain Access Switch Configurations:")
        display_device_configurations(main_switch_configurations)

        print("Topology created.")
        return access_graph, top_graph, device_configurations, top_layer_configurations

    def draw_topology(self):
        """
        Visualize the created network topology.
        """
        print("Visualizing the network topology...")
        visualize_graph(self.access_graph, "Three-Tier Network Topology")

    def get_device_configuration(self, device_name):
        """

        :param device_name:
        :return: the device configuration requested
        """
        return next((config for config in self.access_device_config if config["name"] == device_name), None)


# Example usage
if __name__ == "__main__":
    num_routers = 2
    num_mls = 2
    num_switches = 4
    num_computers = 15
    mode = 1  # 0 for fault-tolerant, 1 for scalable
    ip_base = "192.168.0.0"

    print("Starting GraphManager...")
    graph_manager = GraphManager(num_routers, num_mls, num_switches, num_computers, mode, ip_base)
    graph_manager.draw_topology()
    print("GraphManager finished execution.")
