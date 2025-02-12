#add store-and-forward.
#add_deletion_of_running_congig_+_vlans
#wr er
#delete flash:vlan.dat
#check if dynamic auto is enabled
#add switchport nonegotiate
import ipaddress
import networkx as nx


def configure_top_layers(G, main_access_configs):
    """
    Given:
      - A NetworkX graph G that has 'layer' attributes for each node (Core/Distribution/Access).
      - A list of main access switch configurations (with VLAN ID, IP address, gateway, etc.)
    This function:
      1) Extracts VLAN info from the main access switch configurations.
      2) Identifies and configures Distribution-layer devices with SVIs for inter-VLAN routing.
      3) Identifies and configures Core-layer devices with minimal routing.
      4) Assigns new IP addresses for distribution->core links from subnets following the last used subnet.
      5) Returns a list of device_configurations in a standard format.
    """

    # ---------------------------------------------------------------------
    # 1. Parse Access Switch VLAN information
    # ---------------------------------------------------------------------
    # Each main access switch config has, for example:
    #   {
    #       "Name": "Switch_1",
    #       "Type": "Switch",
    #       "IP Address": "192.168.0.2",
    #       "Subnet Mask": 28,
    #       "VLAN ID": 1,
    #       "Gateway": "192.168.0.1"
    #   }
    #
    # We'll store them in a dict keyed by VLAN ID:
    #
    # vlans_info = {
    #     1: {"gateway": "192.168.0.1", "subnet": "192.168.0.0/28"},
    #     2: {"gateway": "192.168.0.17","subnet": "192.168.0.16/28"},
    #     ...
    # }
    #
    # We'll also figure out the last subnet used so we can assign new subnets
    # to the top-layer devices.

    vlans_info = {}
    highest_subnet = None

    for sw_conf in main_access_configs:
        vlan_id = sw_conf["VLAN ID"]
        gateway = ipaddress.ip_address(sw_conf["Gateway"])
        subnet_mask = sw_conf["Subnet Mask"]

        # Reconstruct the network from Gateway + Subnet Mask
        # Example: 192.168.0.1 with /28
        net = ipaddress.ip_network(f"{gateway}/{subnet_mask}", strict=False)
        vlans_info[vlan_id] = {
            "gateway": str(gateway),
            "subnet": str(net)
        }

        # Track the highest subnet to know where to start next
        if highest_subnet is None:
            highest_subnet = net
        else:
            # Compare which one is "later" in address space
            if list(highest_subnet.hosts())[-1] < list(net.hosts())[-1]:
                highest_subnet = net

    # For example, if the last VLAN used 192.168.0.32/28,
    # highest_subnet = ip_network("192.168.0.32/28")

    # ---------------------------------------------------------------------
    # 2. Identify next subnet (for distribution->core links, etc.)
    # ---------------------------------------------------------------------
    # We'll assume we just move sequentially by /28 blocks. If your design
    # uses a different block size or approach to IP assignment, adjust here.

    def get_next_subnet(network, step=16):
        """
        Given an IPv4Network 'network' with a /28 mask (16 addresses),
        return the next /28 in sequence. By default, each /28 is 16 IPs apart.
        """
        # Convert to integer, add 'step' for next block, then re-cast to network
        next_network_int = int(network.network_address) + (step)
        return ipaddress.ip_network(f"{ipaddress.ip_address(next_network_int)}/{network.prefixlen}")

    # We'll define a generator that keeps giving us new subnets as we call next()
    def subnet_generator(start_net):
        current = start_net
        while True:
            # next block
            current = get_next_subnet(current, step=2 ** (32 - current.prefixlen))
            yield current

    # Create a generator that starts from the highest_subnet
    gen = subnet_generator(highest_subnet)

    # ---------------------------------------------------------------------
    # 3. Build device configurations
    #    For distribution layer:
    #       - Create SVI for each VLAN (with IP = VLAN gateway).
    #    For core layer:
    #       - Minimal routing, or IP addresses on interfaces to connect to Distribution.
    # ---------------------------------------------------------------------

    device_configurations = []

    # Helper to create a device config dict
    def new_device_config_dict(device_name):
        return {
            "device_name": device_name,
            "config_lines": []
        }

    # We'll gather distribution and core devices from the graph
    dist_devices = [n for n, data in G.nodes(data=True) if data.get('layer') == 'Distribution']
    core_devices = [n for n, data in G.nodes(data=True) if data.get('layer') == 'Core']

    # ---------------------------------------------------------------------
    # 3A. Configure Distribution devices
    #     - For each distribution device, we create SVIs for each VLAN.
    #     - The IP for each SVI is the "gateway" from the main VLAN info.
    # ---------------------------------------------------------------------

    for dist_dev in dist_devices:
        cfg = new_device_config_dict(dist_dev)

        # Example lines:
        # interface Vlan1
        #   ip address 192.168.0.1 255.255.255.240
        # interface Vlan2
        #   ip address 192.168.0.17 255.255.255.240
        #
        # We'll take that from the vlans_info stored above.

        for vlan_id, vlan_data in vlans_info.items():
            subnet_str = vlan_data["subnet"]
            gateway_str = vlan_data["gateway"]
            net = ipaddress.ip_network(subnet_str, strict=False)
            mask = net.netmask

            cfg["config_lines"].append(f"interface vlan {vlan_id}")
            cfg["config_lines"].append(f" ip address {gateway_str} {mask}")
            cfg["config_lines"].append(" no shutdown")
            cfg["config_lines"].append("!")

        # You might also want to enable IP routing on a multi-layer switch:
        cfg["config_lines"].append("ip routing")
        cfg["config_lines"].append("!")

        device_configurations.append(cfg)

    # ---------------------------------------------------------------------
    # 3B. Configure Core devices
    #     - We only need minimal routing. Typically we’d set up routing
    #       so the Core can reach the VLAN subnets.
    #     - We'll also assign IP addresses to the Core for each link
    #       connecting to Dist. We pull new subnets from the generator for
    #       Dist-Core connections.
    # ---------------------------------------------------------------------
    #
    # Strategy: For each Core device, see which Dist devices connect to it
    # in the graph. For each Dist<->Core link, we'll allocate a /28
    # from the generator. Then assign the .1 to Dist, .2 to Core
    # (or vice versa—just be consistent).

    used_dist_core_subnets = {}  # (dist_dev, core_dev) -> ip_network

    # We will iterate over edges Dist->Core from the graph.
    # For each pair, get a new /28 and assign addresses.
    #
    # Because the graph is likely undirected or DiGraph, we can just filter
    # edges where one side is Dist, other side is Core.

    for dist_dev in dist_devices:
        for core_dev in core_devices:
            if G.has_edge(dist_dev, core_dev):
                # fetch next /28
                new_net = next(gen)
                used_dist_core_subnets[(dist_dev, core_dev)] = new_net
                used_dist_core_subnets[(core_dev, dist_dev)] = new_net  # store both ways for convenience

    # Now that we have a dictionary of subnets, let's produce the interface
    # config lines on each device. We'll store them in a structure first,
    # then merge them into the final device_configurations.

    dist_interface_cfg = {d: [] for d in dist_devices}  # Dist device -> list of lines
    core_interface_cfg = {c: [] for c in core_devices}  # Core device -> list of lines

    for (dist_dev, core_dev), net in used_dist_core_subnets.items():
        # We only want to proceed in one direction (dist_dev->core_dev),
        # so skip the reversed duplicate
        if dist_devices.count(dist_dev) == 1 and core_devices.count(core_dev) == 1:
            # we know dist_dev is dist, core_dev is core
            pass
        else:
            # If we picked up reversed pairs, we can skip them.
            # A simple way: only handle if dist_dev < core_dev (string compare)
            # or something similar. For clarity, let's skip if dist_dev>core_dev
            if dist_dev > core_dev:
                continue

        # We'll assign .1 to Distribution, .2 to Core
        dist_ip = list(net.hosts())[0]  # e.g. x.x.x.1
        core_ip = list(net.hosts())[1]  # e.g. x.x.x.2
        mask = net.netmask

        # Build interface naming. For real devices,
        # you'd pick the actual interface connecting dist<->core.
        # As a simplified approach, we might label them arbitrarily:
        # Dist side: interface GigabitEthernet0/1 (example)
        # Core side: interface GigabitEthernet0/1
        # Or embed your own logic for naming. We'll do placeholders:
        dist_interface_name = f"Gig0/1_to_{core_dev}"
        core_interface_name = f"Gig0/1_to_{dist_dev}"

        # Store lines
        dist_interface_cfg[dist_dev].append(f"interface {dist_interface_name}")
        dist_interface_cfg[dist_dev].append(f" ip address {dist_ip} {mask}")
        dist_interface_cfg[dist_dev].append(" no shutdown")
        dist_interface_cfg[dist_dev].append("!")

        core_interface_cfg[core_dev].append(f"interface {core_interface_name}")
        core_interface_cfg[core_dev].append(f" ip address {core_ip} {mask}")
        core_interface_cfg[core_dev].append(" no shutdown")
        core_interface_cfg[core_dev].append("!")

    # Merge dist_interface_cfg into device_configurations
    for dev_cfg in device_configurations:
        dname = dev_cfg["device_name"]
        if dname in dist_interface_cfg:
            dev_cfg["config_lines"].extend(dist_interface_cfg[dname])

    # Create core configs
    for core_dev in core_devices:
        cfg = new_device_config_dict(core_dev)

        # Minimal routing lines + interface addresses
        cfg["config_lines"].append("ip routing")
        cfg["config_lines"].append("!")
        # Add the interface lines we stored
        if core_dev in core_interface_cfg:
            cfg["config_lines"].extend(core_interface_cfg[core_dev])

        # Optionally add static routes for VLAN subnets:
        # For each VLAN's subnet, point to Dist IP (the .1 for that link).
        for vlan_id, vlan_data in vlans_info.items():
            net = ipaddress.ip_network(vlan_data["subnet"], strict=False)
            # We might guess the next-hop is whichever distribution IP
            # the core is connected to. If there's more than one distribution,
            # in real life you'd have an IGP or multiple static routes.
            # For demonstration, we pick the first Dist device if it exists:
            if dist_devices:
                dist_dev = dist_devices[0]
                # Find the assigned IP address for dist_dev in used_dist_core_subnets
                # that links to this core device
                if (dist_dev, core_dev) in used_dist_core_subnets:
                    link_net = used_dist_core_subnets[(dist_dev, core_dev)]
                    dist_ip = list(link_net.hosts())[0]  # .1
                    cfg["config_lines"].append(
                        f"ip route {net.network_address} {net.netmask} {dist_ip}"
                    )

        device_configurations.append(cfg)

    return device_configurations

# ------------------------------------------------------------------------
# USAGE EXAMPLE (pseudo):
#
# Suppose you've already built your topology graph 'G' using your
# build_topology() function. Also suppose you have your main_access_configs
# as shown:
#
# main_access_configs = [
#     {
#         "Name": "Switch_1",
#         "Type": "Switch",
#         "IP Address": "192.168.0.2",
#         "Subnet Mask": 28,
#         "VLAN ID": 1,
#         "Gateway": "192.168.0.1"
#     },
#     ...
# ]
#
# device_confs = configure_top_layers(G, main_access_configs)
#
# for dev_conf in device_confs:
#     print("Device:", dev_conf["device_name"])
#     for line in dev_conf["config_lines"]:
#         print(line)
#     print("-----")
# ------------------------------------------------------------------------
