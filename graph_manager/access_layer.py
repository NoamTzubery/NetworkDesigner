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
        valid_edges = [edge for edge in edges if edge[1] not in visited]
        edge = min(valid_edges, key=lambda x: x[2])  # Get the edge with the minimum weight

        # Add the edge to the MST
        mst.add_edge(edge[0], edge[1], weight=edge[2])
        visited.add(edge[1])

        for neighbor in graph.neighbors(edge[1]):
            if neighbor not in visited:
                edges.append((edge[1], neighbor, graph[edge[1]][neighbor]['weight']))
    return mst


def create_fault_tolerant_network(switches, computers):
    """
    Create a fault-tolerant network with redundancy using the given switches and computers.
    """
    G = nx.Graph()
    G.add_nodes_from(switches)
    G.add_nodes_from(computers)

    # Fully connect all switches for fault tolerance
    for i in range(len(switches)):
        for j in range(i + 1, len(switches)):
            G.add_edge(switches[i], switches[j])

    # Connect each computer to two switches for redundancy
    if switches:
        for i, computer in enumerate(computers):
            primary_switch = switches[i % len(switches)]
            # Use a different switch if possible
            secondary_switch = switches[(i + 1) % len(switches)] if len(switches) > 1 else switches[0]
            G.add_edge(computer, primary_switch)
            if primary_switch != secondary_switch:
                G.add_edge(computer, secondary_switch)
    return G


def create_scalable_network(switches, computers):
    """
    Create a scalable network using a spanning tree with the given switches and computers.
    """
    G = nx.Graph()
    G.add_nodes_from(switches)
    G.add_nodes_from(computers)

    # Fully connect the switches with weights for the MST calculation
    for i in range(len(switches)):
        for j in range(i + 1, len(switches)):
            G.add_edge(switches[i], switches[j], weight=i + j)

    # Generate a minimal spanning tree for the switches using Prim's algorithm
    if switches:
        mst = prims_minimum_spanning_tree(G.subgraph(switches))
        # Create a new graph with the MST and then add computers
        H = nx.Graph()
        H.add_nodes_from(mst.nodes())
        H.add_edges_from(mst.edges(data=True))
        # Connect each computer to one switch for scalability (round-robin)
        for i, computer in enumerate(computers):
            H.add_edge(computer, switches[i % len(switches)])
        return H
    else:
        return G


def bin_packing_vlans(switch_count, computer_count):
    """
    Distribute switches and computers across VLANs in a simple round-robin fashion.
    """
    switches = [f"Switch_{i + 1}" for i in range(switch_count)]
    computers = [f"Computer_{i + 1}" for i in range(computer_count)]
    devices = switches + computers
    num_vlans = math.ceil(len(devices) / 7)

    vlans = [[] for _ in range(num_vlans)]
    for i, device in enumerate(devices):
        vlans[i % num_vlans].append(device)

    for i, vlan in enumerate(vlans, start=1):
        print(f"VLAN {i}: {', '.join(vlan)}")
    return vlans


def create_optimal_vlan_network(switch_count, computer_count, mode):
    """
    Determine the optimal number of VLANs and create their topologies based on the mode.
    The original device names are kept and only a 'vlan' attribute is added to each node.
    """
    vlans = bin_packing_vlans(switch_count, computer_count)
    G = nx.Graph()
    vlan_mapping = {}  # Dictionary to store VLAN assignment per node

    for vlan_id, vlan_devices in enumerate(vlans):
        # Separate the devices into switches and computers
        vlan_switches = [d for d in vlan_devices if "Switch" in d]
        vlan_computers = [d for d in vlan_devices if "Computer" in d]

        if mode == 0:  # Fault-tolerant
            vlan_graph = create_fault_tolerant_network(vlan_switches, vlan_computers)
        elif mode == 1:  # Scalable
            vlan_graph = create_scalable_network(vlan_switches, vlan_computers)
        else:
            raise ValueError("Invalid mode. Use 0 for fault-tolerant or 1 for scalable.")

        # Set the VLAN attribute for each node (original names are preserved)
        for node in vlan_graph.nodes():
            vlan_mapping[node] = vlan_id + 1  # VLAN IDs start from 1

        G = nx.compose(G, vlan_graph)

    nx.set_node_attributes(G, vlan_mapping, "vlan")
    return G, vlans


def visualize_graph(G, title):
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    node_colors = [G.nodes[node].get("vlan", 0) for node in G.nodes()]
    nx.draw(
        G, pos, with_labels=True, node_color=node_colors,
        edge_color='gray', node_size=2000, font_weight='bold', cmap=plt.cm.Paired
    )
    plt.title(title, fontsize=16)
    plt.show()


# Example Usage
"""
switch_count = 4
computer_count = 15
mode = 1  # 0 for fault-tolerant, 1 for scalable

optimal_vlan_graph, vlans = create_optimal_vlan_network(switch_count, computer_count, mode)
visualize_graph(optimal_vlan_graph, "Optimal VLAN-Based Network")

# Print VLAN assignments using the original device names
for node, vlan_id in optimal_vlan_graph.nodes(data="vlan"):
    print(f"{node} -> VLAN {vlan_id}")
"""