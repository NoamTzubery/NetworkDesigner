import networkx as nx
import matplotlib.pyplot as plt
import math


def prims_minimum_spanning_tree(graph):
    """
    Implement Prim's algorithm to find the minimum spanning tree of a graph.
    """
    mst = nx.Graph()
    nodes = list(graph.nodes())

    # Start with the first node in the graph
    visited = {nodes[0]}
    edges = []

    # Add all edges from the starting node to the edge list
    for neighbor in graph.neighbors(nodes[0]):
        edges.append((nodes[0], neighbor, graph[nodes[0]][neighbor]['weight']))

    # Keep track of visited nodes and form the MST
    while len(visited) < len(nodes):
        # Find the smallest edge connecting the visited set to the unvisited set
        edges = [edge for edge in edges if edge[1] not in visited]
        edge = min(edges, key=lambda x: x[2])  # Get the edge with the minimum weight

        # Add the edge to the MST
        mst.add_edge(edge[0], edge[1], weight=edge[2])

        # Mark the node as visited
        visited.add(edge[1])

        # Add new edges from the newly visited node
        for neighbor in graph.neighbors(edge[1]):
            if neighbor not in visited:
                edges.append((edge[1], neighbor, graph[edge[1]][neighbor]['weight']))

    return mst


def create_vlan_topology(vlan_switches, vlan_computers):
    """
    Create a topology for a single VLAN.
    """
    G = nx.Graph()

    # If no switches are available, add a placeholder switch
    if not vlan_switches:
        vlan_switches.append("Placeholder_Switch")

    # Add switches
    G.add_nodes_from(vlan_switches)

    # Add computers
    G.add_nodes_from(vlan_computers)

    # Fully connect the switches
    for i in range(len(vlan_switches)):
        for j in range(i + 1, len(vlan_switches)):
            G.add_edge(vlan_switches[i], vlan_switches[j], weight=1)

    # Connect each computer to a switch
    for i, computer in enumerate(vlan_computers):
        G.add_edge(computer, vlan_switches[i % len(vlan_switches)], weight=1)

    return G


def bin_packing_vlans(switch_count, computer_count):
    """
    Distribute switches and computers across VLANs in a simple round-robin fashion.
    """
    # Create lists for switches and computers
    switches = [f"Switch_{i + 1}" for i in range(switch_count)]
    computers = [f"Computer_{i + 1}" for i in range(computer_count)]

    # Combine all devices
    devices = switches + computers

    # Calculate the number of VLANs needed
    num_vlans = math.ceil(len(devices) / 7)

    # Initialize empty VLANs
    vlans = [[] for _ in range(num_vlans)]

    # Assign devices to VLANs in a round-robin manner
    for i, device in enumerate(devices):
        vlans[i % num_vlans].append(device)

    return vlans


def create_optimal_vlan_network(switch_count, computer_count):
    """
    Determine the optimal number of VLANs and create their topologies.
    """
    # Bin-pack devices into VLANs
    vlans = bin_packing_vlans(switch_count, computer_count)

    G = nx.Graph()

    # Create topologies for each VLAN
    for vlan_id, vlan_devices in enumerate(vlans):
        vlan_switches = [d for d in vlan_devices if "Switch" in d]
        vlan_computers = [d for d in vlan_devices if "Computer" in d]

        vlan_graph = create_vlan_topology(vlan_switches, vlan_computers)

        # Relabel nodes to include VLAN information
        mapping = {node: f"VLAN{vlan_id + 1}_{node}" for node in vlan_graph.nodes}
        vlan_graph = nx.relabel_nodes(vlan_graph, mapping)

        # Add VLAN graph to the main graph
        G = nx.compose(G, vlan_graph)

    return G, vlans


def visualize_graph(G, title):
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    nx.draw(
        G, pos, with_labels=True, node_color='lightblue',
        edge_color='gray', node_size=2000, font_weight='bold'
    )
    plt.title(title, fontsize=16)
    plt.show()


# Example Usage
switch_count = 8
computer_count = 11

# Generate optimal VLAN-based network
optimal_vlan_graph, vlans = create_optimal_vlan_network(switch_count, computer_count)
visualize_graph(optimal_vlan_graph, "Optimal VLAN-Based Network")

# Print VLANs
for i, vlan in enumerate(vlans):
    print(f"VLAN {i + 1}: {vlan}")
