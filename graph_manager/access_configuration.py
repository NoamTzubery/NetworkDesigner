import math
import telnetlib
import time

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


def configure_device_via_telnet(device_name, port, device_configurations):
    """
    Configure a network device using Telnet based on its stored configuration.

    :param device_name: The name of the device to configure.
    :param port: The local port assigned to this device.
    :param device_configurations: A list of dictionaries containing device configurations.
    """
    # Find the device in the configurations
    device = next((d for d in device_configurations if d["name"] == device_name), None)

    if not device:
        print(f"Error: Device '{device_name}' not found in configurations.")
        return

    device_type = device["type"]
    ip_address = device.get("ip_address")
    subnet_mask = device.get("subnet_mask")
    gateway = device.get("gateway")
    vlan_id = device.get("vlan_id", None)  # Only for switches

    try:
        port = int(port)  # Ensure port is a number
    except ValueError:
        print(f"Invalid port number: {port}. Please enter a valid number.")
        return

    print(f"\nConnecting to {device_name} on localhost:{port} via Telnet...")

    try:
        # Open Telnet session to the local device
        tn = telnetlib.Telnet("localhost", port, timeout=5)
        time.sleep(1)  # Allow connection to establish

        if device_type.lower() == "switch":
            print(f"Configuring {device_name} as a Switch...")

            # Enter privileged mode
            tn.write(b"enable\n")
            time.sleep(1)
            tn.write(b"configure terminal\n")
            time.sleep(1)

            # Apply VLAN configuration if available
            if vlan_id:
                tn.write(f"vlan {vlan_id}\n".encode('ascii'))
                time.sleep(1)

            # Set Store-and-Forward Mode
            tn.write(b"spanning-tree mode mst\n")
            time.sleep(1)
            tn.write(b"spanning-tree forwarding-mode store-and-forward\n")
            time.sleep(1)

            # Save configuration
            tn.write(b"exit\n")
            time.sleep(1)
            tn.write(b"write memory\n")
            time.sleep(1)

        elif device_type.lower() == "computer":
            if not ip_address or not subnet_mask or not gateway:
                print(f"Skipping configuration for {device_name}: Missing network parameters.")
                tn.close()
                return

            print(f"Configuring {device_name} as a Computer...")

            # Assign IP and Subnet Mask
            tn.write(f"ifconfig eth0 {ip_address} netmask {subnet_mask}\n".encode('ascii'))
            time.sleep(1)

            # Assign Default Gateway
            tn.write(f"route add default gw {gateway}\n".encode('ascii'))
            time.sleep(1)

        else:
            print(f"Unknown device type: {device_type}. Skipping configuration.")
            tn.close()
            return

        # Close Telnet session
        tn.write(b"exit\n")
        tn.close()
        print(f"Configuration applied to {device_name} successfully.")

    except Exception as e:
        print(f"Failed to configure {device_name} at localhost:{port}. Error: {e}")
