import networkx as nx
import matplotlib.pyplot as plt


def create_top_two_layers(distribution, core, main_access_switches):
    """
    Creates the top two layers (Distribution and Core) of a 3-tier network topology.

    :param distribution: List of distribution layer devices
    :param core: List of core layer devices
    :param main_access_switches: List of main access switches to connect to the distribution layer
    :return: A NetworkX graph representing the top two layers
    """
    print("Creating the top two layers of the network topology...")
    G = nx.DiGraph()  # Directed graph for clear hierarchy

    # Add Core and Distribution nodes
    G.add_nodes_from(core, layer='Core')
    G.add_nodes_from(distribution, layer='Distribution')

    # Add edges between Core and Distribution layers
    for core_device in core:
        for dist_device in distribution:
            G.add_edge(core_device, dist_device)

    # Add Access nodes and connect them to Distribution nodes
    G.add_nodes_from(main_access_switches, layer='Access')
    for dist_device in distribution:
        for access_switch in main_access_switches:
            G.add_edge(dist_device, access_switch)  # Access connects only to Distribution

    print("Top two layers created successfully!")
    return G


def draw_topology(G):
    """
    Visualizes the graph with a layered structure.

    :param G: A NetworkX graph representing the network topology
    """
    pos = {}  # Custom position for each node to create a layered structure

    # Define layers with fixed y-coordinates
    layers = {
        'Core': 0.9,
        'Distribution': 0.6,
        'Access': 0.3
    }

    # Assign layers to nodes
    # Default to the "Access" layer if the 'layer' attribute is missing
    node_layers = {node: data.get('layer', 'Access') for node, data in G.nodes(data=True)}

    # Separate nodes by their layer
    core_nodes = [node for node, layer in node_layers.items() if layer == 'Core']
    distribution_nodes = [node for node, layer in node_layers.items() if layer == 'Distribution']
    access_nodes = [node for node, layer in node_layers.items() if layer == 'Access']

    # Define horizontal spacing for clarity
    spacing = 1.5
    pos.update({node: (i * spacing, layers['Core']) for i, node in enumerate(core_nodes)})
    pos.update({node: (i * spacing, layers['Distribution']) for i, node in enumerate(distribution_nodes)})
    pos.update({node: (i * spacing, layers['Access']) for i, node in enumerate(access_nodes)})

    # Ensure all nodes have positions
    for node in G.nodes():
        if node not in pos:
            pos[node] = (0, 0)  # Assign a default position for safety

    # Draw the graph
    plt.figure(figsize=(12, 8))
    nx.draw_networkx_nodes(G, pos, node_size=700, node_color='skyblue')
    nx.draw_networkx_edges(G, pos, edge_color='gray')
    nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
    plt.title("Top Two Layers - Network Topology Visualization", fontsize=14)
    plt.axis('off')
    plt.show()


# Debug file
if __name__ == "__main__":
    # Example lists for testing
    distribution_devices = ["Dist_1", "Dist_2"]
    core_devices = ["Core_1", "Core_2"]
    main_access_switches = ["Access_1", "Access_2", "Access_3"]

    # Create the graph for the top two layers
    G = create_top_two_layers(distribution_devices, core_devices, main_access_switches)

    # Draw the graph
    draw_topology(G)
