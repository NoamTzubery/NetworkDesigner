import networkx as nx
import matplotlib.pyplot as plt


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
    # Connect Distribution to Access
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


if __name__ == "__main__":
    # Define devices in each layer
    core_devices = ["Core_1", "Core_2"]  # Change to an empty list to test two-tier topology
    distribution_devices = ["Dist_1", "Dist_2", "Dist_3"]
    access_switches = ["Access_1", "Access_2", "Access_3", "Access_4"]

    # Build and visualize the topology
    network_graph = build_topology(core_devices, distribution_devices, access_switches)
    draw_topology(network_graph)
