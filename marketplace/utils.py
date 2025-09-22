import random
import string

def get_name_id(obj):
    """
    # Cria o name_id = vnf_name-version-developer
    """

    return '-'.join([str(obj.VNF_name), str(obj.version), str(obj.developer)]) \
              .replace(' ', '')

def unique_id():
    """
    Generate a unique string
    """

    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))


acls = {
    "eth_type": {
        "type": "string",
        "description": "Specifies Ethernet frame type (See IEEE 802.3)"
    },

    "eth_src": {
        "type": "string",
        "description": "Ethernet source address"
    },

    "eth_dst": {
        "type": "string",
        "description": "Ethernet destination address"
    },

    "vlan_id": {
        "type": "integer",
        "in_range": [1, 4094],
        "description": "VLAN ID"
    },

    "vlan_pcp": {
        "type": "integer",
        "in_range": [0, 7],
        "description": "VLAN Priority"
    },

    "mpls_label": {
        "type": "integer",
        "in_range": [16, 1048575],
        "description": "MPLS Label"
    },

    "mpls_tc": {
        "type": "integer",
        "in_range": [0, 7],
        "description": "MPLS Traffic Class"
    },

    "ip_dscp": {
        "type": "integer",
        "in_range": [0, 63],
        "description": "IP DSCP (6 bits in ToS field)"
    },

    "ip_ecn": {
        "type": "integer",
        "in_range": [0, 3],
        "description": "IP ECN (2 bits in ToS field)"
    },

    "ip_src_prefix": {
        "type": "string",
        "description": "IP source address prefix"
    },

    "ip_dst_prefix": {
        "type": "string",
        "description": "IP destination address prefix"
    },

    "ip_proto": {
        "type": "integer",
        "in_range": [1, 254],
        "description": "IP protocol number"
    },

    "destination_port_range": {
        "type": "string",
        "description": "Destination port range"
    },

    "source_port_range": {
        "type": "string",
        "description": "Source port range"
    },

    "network_id": {
        "type": "string",
        "description": "Network ID"
    },

    "network_name": {
        "type": "string",
        "description": "Network name"
    },

    "network_src_port_id": {
        "type": "string",
        "description": "Network Source Port ID"
    },

    "tenant_id": {
        "type": "string",
        "description": "OpenStack Tenant ID"
    },

    "icmpv4_type": {
        "type": "integer",
        "in_range": [0, 254],
        "description": "ICMP type"
    },

    "icmpv4_code": {
        "type": "integer",
        "in_range": [0, 15],
        "description": "ICMP code"
    },

    "arp_op": {
        "type": "integer",
        "in_range": [1, 25],
        "description": "ARP opcode"
    },

    "arp_spa": {
        "type": "string",
        "description": "ARP source ipv4 address"
    },

    "arp_tpa": {
        "type": "string",
        "description": "ARP target ipv4 address"
    },

    "arp_sha": {
        "type": "string",
        "description": "ARP source hardware address"
    },

    "arp_tha": {
        "type": "string",
        "description": "ARP target hardware address"
    },

    "ipv6_src": {
        "type": "string",
        "description": "IPv6 source address"
    },

    "ipv6_dst": {
        "type": "string",
        "description": "IPv6 destination address"
    },

    "ipv6_flabel": {
        "type": "integer",
        "in_range": [0, 1048575],
        "description": "IPv6 Flow Label"
    },

    "icmpv6_type": {
        "type": "integer",
        "in_range": [0, 255],
        "description": "ICMPv6 type"
    },

    "icmpv6_code": {
        "type": "integer",
        "in_range": [0, 7],
        "description": "ICMPv6 code"
    },

    "ipv6_nd_target": {
        "type": "string",
        "description": "Target address for ND"
    },

    "ipv6_nd_sll": {
        "type": "string",
        "description": "Source link-layer for ND"
    },

    "ipv6_nd_tll": {
        "type": "string",
        "description": "Target link-layer for ND"
    }
}
