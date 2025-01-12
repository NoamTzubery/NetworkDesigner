import math

# Constants
MIN_BITS_FOR_NETWORK_BROADCAST = 2
BYTE_MASK = 0xFF
BITS_IN_BYTE = 8
MAX_BITS_IN_IP = 32
DEVICE_TYPE_SWITCH = "Switch"
DEVICE_TYPE_COMPUTER = "Computer"


def calculate_subnet_size(hosts):
    """
    Calculate the size of a subnet given the number of hosts.
    Includes room for network and broadcast addresses.
    """
    return 2 ** math.ceil(
        math.log2(hosts + MIN_BITS_FOR_NETWORK_BROADCAST))  # +2 accounts for network and broadcast addresses


def ip_to_int(ip):
    """
    Convert an IP address from dotted decimal format to an integer.
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
    subnet_sizes = sorted([calculate_subnet_size(hosts) for hosts in total_hosts], reverse=True)
    current_ip = ip_to_int(ip_base)
    subnets = []

    for size in subnet_sizes:
        subnet_mask = MAX_BITS_IN_IP - int(math.log2(size))
        subnets.append({
            "range": f"{int_to_ip(current_ip)}/{subnet_mask}",
            "first_ip": int_to_ip(current_ip + 1),
            "last_ip": int_to_ip(current_ip + size - MIN_BITS_FOR_NETWORK_BROADCAST),
            "subnet_mask": subnet_mask,
            "size": size,
        })
        current_ip += size

    return subnets


def assign_ip_to_device(device_name, base_ip, offset):
    """
    Assign an IP address to a device based on a base IP and an offset.
    """
    assigned_ip = int_to_ip(ip_to_int(base_ip) + offset)
    return {
        "name": device_name,
        "type": DEVICE_TYPE_SWITCH if DEVICE_TYPE_SWITCH in device_name else DEVICE_TYPE_COMPUTER,
        "ip_address": assigned_ip,
    }


def configure_devices(vlans, ip_base):
    """
    Configure all devices with IPs, VLANs, and prepare for Telnet.
    """
    total_hosts = [len(vlan) for vlan in vlans]
    vlsm_subnets = calculate_vlsm(ip_base, total_hosts)

    device_configurations = []
    for vlan_id, (vlan_devices, subnet) in enumerate(zip(vlans, vlsm_subnets), start=1):
        gateway_ip = subnet["first_ip"]
        for i, device in enumerate(vlan_devices):
            device_config = assign_ip_to_device(device, gateway_ip, i)
            device_config.update({
                "subnet_mask": subnet["subnet_mask"],
                "vlan_id": vlan_id,
                "gateway": gateway_ip,
            })
            device_configurations.append(device_config)

    return device_configurations


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
