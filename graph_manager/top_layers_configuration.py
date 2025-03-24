import math
import networkx as nx
import matplotlib.pyplot as plt

# Constants for network configuration
MAX_BITS_IN_IP = 32
BYTE_MASK = 0xFF
BITS_IN_BYTE = 8
MIN_BITS_FOR_NETWORK_BROADCAST_AND_GATEWAY = 2  # Adjusted to 2 for network, broadcast, and gateway addresses


def calculate_subnet_size(hosts):
    """
    Calculate the size of a subnet given the number of hosts.
    """
    return 2 ** math.ceil(math.log2(hosts + MIN_BITS_FOR_NETWORK_BROADCAST_AND_GATEWAY))


def ip_to_int(ip: str) -> int:
    """
    Convert an IP address from dotted decimal to integer format.
    """
    octets = list(map(int, ip.split('.')))
    return (octets[0] << (BITS_IN_BYTE * 3)) | (octets[1] << (BITS_IN_BYTE * 2)) | (octets[2] << BITS_IN_BYTE) | octets[3]


def int_to_ip(ip_int):
    """
    Convert an integer to an IP address in dotted decimal format.
    """
    return f"{(ip_int >> (BITS_IN_BYTE * 3)) & BYTE_MASK}." \
           f"{(ip_int >> (BITS_IN_BYTE * 2)) & BYTE_MASK}." \
           f"{(ip_int >> BITS_IN_BYTE) & BYTE_MASK}." \
           f"{ip_int & BYTE_MASK}"


def assign_ip_to_device(device_name, base_ip, offset):
    """
    Assign an IP address to a device based on a base IP and an offset.
    """
    base_ip_int = ip_to_int(base_ip)
    assigned_ip_int = base_ip_int + offset
    assigned_ip = int_to_ip(assigned_ip_int)

    device_type = "Core" if "Core" in device_name else "Distribution" if "Dist" in device_name else "Access"

    return assigned_ip, device_type


def create_device_config(device_name, device_type, assigned_ip, subnet_mask, connections_count):
    """
    Create the configuration for each device (either Core or Distribution).
    """
    return {
        "name": device_name,
        "type": device_type,
        "ip_address": assigned_ip,
        "subnet_mask": subnet_mask,
        "connections_count": connections_count
    }


def configure_top_layers(dist_devices, core_devices, access_switches, ip_base):
    """
    Configure the Core and Distribution layers, including handling collapsed layers.
    """
    device_configurations = []
    num_switches = len(access_switches)
    # Check if we have Core devices
    if core_devices:
        print("Configuring 3-tier network (Core + Distribution)...")
        # Handle 3-tier network: Core + Distribution
        for i, device in enumerate(dist_devices):
            assigned_ip, device_type = assign_ip_to_device(device, ip_base, i)
            device_config = create_device_config(device, device_type, assigned_ip, "255.255.255.0", len(core_devices) + num_switches )
            device_configurations.append(device_config)

        for i, device in enumerate(core_devices):
            assigned_ip, device_type = assign_ip_to_device(device, ip_base, len(dist_devices) + i)
            device_config = create_device_config(device, device_type, assigned_ip, "255.255.255.0", len(dist_devices))
            device_configurations.append(device_config)

    else:
        print("Configuring 2-tier network (Distribution becomes Core)...")
        # Handle 2-tier collapsed network: all devices in dist_devices are now core devices
        for i, device in enumerate(dist_devices):
            assigned_ip, device_type = assign_ip_to_device(device, ip_base, i)
            device_config = create_device_config(device, "Core", assigned_ip, "255.255.255.0", len(dist_devices) + num_switches)
            device_configurations.append(device_config)

    return device_configurations


def display_device_configurations(device_configurations):
    """
    Display the configurations for all devices.
    """
    for device in device_configurations:
        print(f"Name: {device['name']}")
        print(f"Type: {device['type']}")
        print(f"IP Address: {device['ip_address']}")
        print(f"Subnet Mask: {device['subnet_mask']}")
        print(f"Connections Count: {device['connections_count']}")
        print("-" * 30)


# Network topology generation
def create_core_layer(core_devices, dist_devices):
    """
    Connects the Core layer to the Distribution layer.

    :param core_devices: List of Core layer devices
    :param dist_devices: List of Distribution layer devices
    :return: A list of edges connecting Core to Distribution
    """
    edges = []
    for core_device in core_devices:
        for dist_device in dist_devices:
            edges.append((core_device, dist_device))
    return edges


def create_distribution_layer(dist_devices, access_switches):
    """
    Connects the Distribution layer to the Access layer and interconnects Distribution devices.

    :param dist_devices: List of Distribution layer devices
    :param access_switches: List of Access layer switches
    :return: A list of edges connecting Distribution to Access and between Distribution devices
    """
    edges = []
    # Connect Distribution to Access (Main Switches)
    for dist_device in dist_devices:
        for access_switch in access_switches:
            edges.append((dist_device, access_switch))
    # Interconnect Distribution devices for redundancy
    for i in range(len(dist_devices)):
        for j in range(i + 1, len(dist_devices)):
            edges.append((dist_devices[i], dist_devices[j]))
    return edges


def build_topology(core_devices, dist_devices, access_switches):
    """
    Builds a three-tier network topology. If the Core layer is empty,
    collapses the topology to two tiers by moving routing to the Distribution layer.

    :param core_devices: List of Core layer devices
    :param dist_devices: List of Distribution layer devices
    :param access_switches: List of Access layer switches
    :return: A NetworkX DiGraph representing the network topology
    """
    print("Building the network topology...")
    G = nx.DiGraph()

    # Add devices to the graph
    G.add_nodes_from(core_devices, layer='Core')
    G.add_nodes_from(dist_devices, layer='Distribution')
    G.add_nodes_from(access_switches, layer='Access')

    # Create edges based on the layers
    if core_devices:
        # Three-tier topology
        print("Creating a three-tier topology.")
        G.add_edges_from(create_core_layer(core_devices, dist_devices))
    else:
        # Collapsed to two tiers
        print("Core layer is empty, collapsing to two-tier topology.")
        # All distribution devices are now core devices
        for dist_device in dist_devices:
            G.nodes[dist_device]['layer'] = 'Core'

    G.add_edges_from(create_distribution_layer(dist_devices, access_switches))

    print("Network topology built successfully!")
    return G


def draw_topology(G):
    """
    Visualizes the graph with a layered structure.

    :param G: A NetworkX graph representing the network topology
    """
    print("Drawing the network topology...")
    pos = {}
    layers = {
        'Core': 0.9,
        'Distribution': 0.6,
        'Access': 0.3
    }

    # Determine positions for nodes in each layer
    node_layers = {node: data.get('layer', 'Access') for node, data in G.nodes(data=True)}
    spacing = 1.5

    for layer_name, y_coord in layers.items():
        nodes_in_layer = [node for node, layer in node_layers.items() if layer == layer_name]
        for i, node in enumerate(nodes_in_layer):
            pos[node] = (i * spacing, y_coord)

    # Draw the graph
    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(G, pos, node_size=700, node_color='skyblue')
    nx.draw_networkx_edges(G, pos, edge_color='gray')
    nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
    plt.title("Network Topology Visualization", fontsize=14)
    plt.axis('off')
    plt.show()


# Example usage:
"""
core_devices = ["Core_1", "Core_2"]  # Change to an empty list to test two-tier topology
distribution_devices = ["Dist_1", "Dist_2", "Dist_3"]
access_switches = ["Access_1", "Access_2", "Access_3", "Access_4"]
ip_base = "192.168.1.0"  # Base IP for assignment

# Build the topology and configure the devices
device_configurations = configure_top_layers(distribution_devices, core_devices, access_switches, ip_base)

# Display the device configurations
display_device_configurations(device_configurations)

# Build and visualize the topology graph
network_graph = build_topology(core_devices, distribution_devices, access_switches)
draw_topology(network_graph)
"""