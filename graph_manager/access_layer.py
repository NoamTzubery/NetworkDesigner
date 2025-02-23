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


def create_fault_tolerant_network(switch_count, computer_count):
    """
    Create a fault-tolerant network with redundancy.
    """
    G = nx.Graph()

    # Add switches
    switches = [f"Switch_{i}" for i in range(1, switch_count + 1)]
    G.add_nodes_from(switches)

    # Add computers
    computers = [f"Computer_{i}" for i in range(1, computer_count + 1)]
    G.add_nodes_from(computers)

    # Fully connect all switches for fault tolerance
    for i in range(len(switches)):
        for j in range(i + 1, len(switches)):
            G.add_edge(switches[i], switches[j])

    # Connect each computer to two switches for redundancy
    for i, computer in enumerate(computers):
        primary_switch = switches[i % switch_count]
        secondary_switch = switches[(i + 1) % switch_count]
        G.add_edge(computer, primary_switch)
        G.add_edge(computer, secondary_switch)

    return G


def create_scalable_network(switch_count, computer_count):
    """
    Create a scalable network using a spanning tree.
    """
    G = nx.Graph()

    # Add switches
    switches = [f"Switch_{i}" for i in range(1, switch_count + 1)]
    G.add_nodes_from(switches)

    # Add computers
    computers = [f"Computer_{i}" for i in range(1, computer_count + 1)]
    G.add_nodes_from(computers)

    # Fully connect the switches initially
    for i in range(len(switches)):
        for j in range(i + 1, len(switches)):
            G.add_edge(switches[i], switches[j], weight=i + j)

    # Generate a minimal spanning tree for the switches using Prim's algorithm
    mst = prims_minimum_spanning_tree(G.subgraph(switches))

    # Add the spanning tree back to the graph
    G = nx.compose(G.subgraph(computers), mst)

    # Connect each computer to one switch for scalability
    for i, computer in enumerate(computers):
        G.add_edge(computer, switches[i % switch_count])

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
    Determine the optimal number of VLANs and create their topologies based on mode.
    """
    vlans = bin_packing_vlans(switch_count, computer_count)

    G = nx.Graph()
    vlan_mapping = {}  # Dictionary to store VLAN assignment per node

    for vlan_id, vlan_devices in enumerate(vlans):
        vlan_switches = [d for d in vlan_devices if "Switch" in d]
        vlan_computers = [d for d in vlan_devices if "Computer" in d]

        if mode == 0:  # Fault-tolerant
            vlan_graph = create_fault_tolerant_network(len(vlan_switches), len(vlan_computers))
        elif mode == 1:  # Scalable
            vlan_graph = create_scalable_network(len(vlan_switches), len(vlan_computers))
        else:
            raise ValueError("Invalid mode. Use 0 for fault-tolerant or 1 for scalable.")

        # Relabel nodes with VLAN prefix and store VLAN information
        mapping = {node: f"VLAN{vlan_id + 1}_{node}" for node in vlan_graph.nodes}
        vlan_graph = nx.relabel_nodes(vlan_graph, mapping)

        # Add VLAN attribute to nodes
        for node in vlan_graph.nodes():
            vlan_mapping[node] = vlan_id + 1  # VLAN IDs start from 1

        G = nx.compose(G, vlan_graph)

    # Assign VLAN attributes to the nodes in the final graph
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
switch_count = 4
computer_count = 15
mode = 1  # 0 for fault-tolerant, 1 for scalable

optimal_vlan_graph, vlans = create_optimal_vlan_network(switch_count, computer_count, mode)
visualize_graph(optimal_vlan_graph, "Optimal VLAN-Based Network")

# Print VLAN assignments
for node, vlan_id in optimal_vlan_graph.nodes(data="vlan"):
    print(f"{node} -> VLAN {vlan_id}")
