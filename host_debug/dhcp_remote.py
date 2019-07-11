import sys
sys.path.append('../common/')

import discovery
import phy_int
import pcap_driver
import scapy_driver
import time

VIF_PREFIX_LEN = 14
DEV_NAME_LEN = 14
QVB_DEV_PREFIX = "qvo"
DHCP_MESSATE_TYPE = ['', 'DHCPDISCOVER', 'DHCPOFFER', 'DHCPREQUEST',
                              'DHCPDECLINE', 'DHCPACK', 'DHCPNAK', 'DHCPRELEASE']
DHCP_NS_PREFIX = 'qdhcp-'
ARP_OP_TYPE = ['', 'REQUEST', 'REPLY']


def init_dhcp_check(dhcp_dict):
    pcap = pcap_driver.PcapDriver()
    scapy = scapy_driver.ScapyDriver()

    vif_names = {}
    phy_port = phy_int.get_phy_interface(dhcp_dict['bridge_name'])
    vif_names[phy_port] = phy_port

    src_mac = dhcp_dict['src_mac_address']
    filter = "udp port (67 or 68) and ether host %s" % src_mac

    listeners = []
    for k,v in vif_names.items():
        listeners.append(pcap.setup_listener(v, filter))

    # for dhcp_server in dhcp_dict['dhcp local host']:
        ## TODO: Add ports for DHCP tap interface to listeners

    return listeners


def get_sniff_result(listeners,handler):
    data = dict()
    for listener in listeners:
        vif_pre = listener.name
        data["remote host:" + vif_pre] = []
        for packet in listener.readpkts():
            icmp_type = handler(str(packet[1]))
            if icmp_type is not None:
               data[vif_pre].append(icmp_type)
    return data
