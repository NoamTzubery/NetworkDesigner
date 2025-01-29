import math

# Constants
MIN_BITS_FOR_NETWORK_BROADCAST_AND_GATEWAY = 3  # Accounts for network, broadcast, and gateway addresses
BYTE_MASK = 0xFF
BITS_IN_BYTE = 8
MAX_BITS_IN_IP = 32
DEVICE_TYPE_SWITCH = "Switch"
DEVICE_TYPE_COMPUTER = "Computer"


def calculate_subnet_size(hosts):
    """
    Calculate the size of a subnet given the number of hosts.
    Includes room for network, broadcast, and gateway addresses.
    """
    return 2 ** math.ceil(
        math.log2(hosts + MIN_BITS_FOR_NETWORK_BROADCAST_AND_GATEWAY))


def ip_to_int(ip: str) -> int:
    """
    :param ip:
    :return int:
    """
    octets = list(map(int, ip.split('.')))
    return (octets[0] << (BITS_IN_BYTE * 3)) | (octets[1] << (BITS_IN_BYTE * 2)) | (octets[2] << BITS_IN_BYTE) | octets[
        3]


def int_to_ip(ip_int):
    """
    Convert an integer to an IP address in dotted decimal format.
    """
    return f"{(ip_int >> (BITS_IN_BYTE * 3)) & BYTE_MASK}." \
           f"{(ip_int >> (BITS_IN_BYTE * 2)) & BYTE_MASK}." \
           f"{(ip_int >> BITS_IN_BYTE) & BYTE_MASK}." \
           f"{ip_int & BYTE_MASK}"


def calculate_vlsm(ip_base, total_hosts):
    """
    Assign IP ranges using VLSM based on the number of hosts.
    """
    # Step 1: Calculate subnet sizes
    subnet_sizes = []
    for hosts in total_hosts:
        subnet_size = calculate_subnet_size(hosts)
        subnet_sizes.append(subnet_size)

    # Sort subnet sizes in descending order
    sorted_subnet_sizes = sorted(subnet_sizes, reverse=True)

    # Step 2: Convert base IP to integer
    current_ip = ip_to_int(ip_base)

    # Step 3: Initialize subnets
    subnets = []
    for size in sorted_subnet_sizes:
        # Calculate subnet mask
        bits_needed = int(math.log2(size))
        subnet_mask = MAX_BITS_IN_IP - bits_needed

        # Calculate subnet details
        range_ip = int_to_ip(current_ip)
        first_ip = int_to_ip(current_ip + 1)  # Default gateway
        last_ip = int_to_ip(current_ip + size - MIN_BITS_FOR_NETWORK_BROADCAST_AND_GATEWAY)
        subnet_details = {
            "range": f"{range_ip}/{subnet_mask}",
            "first_ip": first_ip,
            "last_ip": last_ip,
            "subnet_mask": subnet_mask,
            "size": size,
        }

        # Append to subnets list
        subnets.append(subnet_details)

        # Update current_ip
        current_ip += size

    # Return final subnets
    return subnets


def assign_ip_to_device(device_name, base_ip, offset):
    """
    Assign an IP address to a device based on a base IP and an offset.
    """
    # Convert base IP to integer
    base_ip_int = ip_to_int(base_ip)

    # Calculate assigned IP
    assigned_ip_int = base_ip_int + offset
    assigned_ip = int_to_ip(assigned_ip_int)

    # Determine device type
    if DEVICE_TYPE_SWITCH in device_name:
        device_type = DEVICE_TYPE_SWITCH
    else:
        device_type = DEVICE_TYPE_COMPUTER

    # Create and return device configuration
    device_config = {
        "name": device_name,
        "type": device_type,
        "ip_address": assigned_ip,
    }
    return device_config


def configure_devices(vlans, ip_base):
    """
    Configure all devices with IPs, VLANs, and prepare for Telnet.
    """
    # Step 1: Calculate total hosts per VLAN
    total_hosts = []
    for vlan in vlans:
        vlan_host_count = len(vlan)
        total_hosts.append(vlan_host_count)

    # Step 2: Calculate VLSM subnets
    vlsm_subnets = calculate_vlsm(ip_base, total_hosts)

    # Step 3: Configure devices
    device_configurations = []
    main_switches = []
    first = True
    for vlan_id, (vlan_devices, subnet) in enumerate(zip(vlans, vlsm_subnets), start=1):
        # Extract subnet details
        gateway_ip = subnet["first_ip"]  # First usable IP is the gateway
        subnet_mask = subnet["subnet_mask"]
        first = True
        # Assign IPs to devices
        for i, device in enumerate(vlan_devices):
            device_config = assign_ip_to_device(device, gateway_ip, i + 1)  # Start assigning from gateway + 1
            if first:
                main_switches.append(device)
                first = False
            # Add additional details to device configuration
            device_config["subnet_mask"] = subnet_mask
            device_config["vlan_id"] = vlan_id
            device_config["gateway"] = gateway_ip

            # Append to final configurations
            device_configurations.append(device_config)

    # Return device configurations
    return device_configurations, main_switches


def display_device_configurations(device_configurations):
    """
    Display configurations for all devices.
    """
    for device in device_configurations:
        print(f"Name: {device['name']}")
        print(f"Type: {device['type']}")
        print(f"IP Address: {device['ip_address']}")
        print(f"Subnet Mask: {device['subnet_mask']}")
        print(f"VLAN ID: {device['vlan_id']}")
        print(f"Gateway: {device['gateway']}")
        print("-" * 30)
