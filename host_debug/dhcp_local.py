import sys
sys.path.append('../common/')

import discovery
import dhcp_port
import phy_int
import pcap_driver
import scapy_driver
import time

VIF_PREFIX_LEN = 14
PORT_ID_PREFEX = 11
DEV_NAME_LEN = 14
QVB_DEV_PREFIX = "qvo"
DHCP_MESSATE_TYPE = ['', 'DHCPDISCOVER', 'DHCPOFFER', 'DHCPREQUEST',
                              'DHCPDECLINE', 'DHCPACK', 'DHCPNAK', 'DHCPRELEASE']
DHCP_NS_PREFIX = 'qdhcp-'
ARP_OP_TYPE = ['', 'REQUEST', 'REPLY']


def init_dhcp_check(dhcp_dict):
    pcap = pcap_driver.PcapDriver()
    scapy = scapy_driver.ScapyDriver()

    port_id = dhcp_dict['vm info']['port_id']
    vif_names = discovery.get_vif_names(port_id)
    phy_port = phy_int.get_phy_interface(dhcp_dict['vm info']['bridge_name'])
    vif_names["local nic:" + phy_port] = phy_port

    src_mac = dhcp_dict['vm info']['mac_address']
    filter = "udp port (67 or 68) and ether host %s" % src_mac

    listeners = []
    for k,v in vif_names.items():
        listeners.append(pcap.setup_listener(v, filter))

    for local_port in dhcp_dict['dhcp local host']:
        port_id = local_port['port_id'][:PORT_ID_PREFEX]
        dhcp_port.create_pcap_file(port_id, dhcp_dict['vm info']['network_id'], dhcp_dict['vm info']['mac_address'])


    inject_packets(scapy, vif_names, src_mac)

    data = get_sniff_result(listeners, scapy.get_dhcp_mt)

    dhcp_port_data = []
    for local_port in dhcp_dict['dhcp local host']:
        port_id = local_port['port_id'][:PORT_ID_PREFEX]
        dhcp_port_data.append(dhcp_port.get_port_data(port_id, "local host:"))

    for port in dhcp_port_data:
        data.update(port)

    return data

def inject_packets(scapy, vif_names, src_mac):
    scapy.send_dhcp_over_qbr(vif_names['qbr'], src_mac)
    time.sleep(1)

def get_sniff_result(listeners,handler):
    data = dict()
    for listener in listeners:
        vif_pre = listener.name
        data["local host:" + vif_pre] = []
        for packet in listener.readpkts():
            icmp_type = handler(str(packet[1]))
            if icmp_type is not None:
               data["local host:" + vif_pre].append(icmp_type)
    return data
