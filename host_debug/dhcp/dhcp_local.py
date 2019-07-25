import sys
sys.path.append('../common/')
sys.path.append('../')

import discovery
import dhcp_port
import phy_int
import pcap_driver
import scapy_driver
import set_listeners
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
    network_type = dhcp_dict['vm info']['network_type']

    vif_names = discovery.get_vif_names(port_id)
    src_mac = dhcp_dict['vm info']['mac_address']
    if dhcp_dict['vm info']['network_type'] == 'vlan':
        phy_port = phy_int.get_phy_interface(dhcp_dict['vm info']['bridge_name'])
    elif dhcp_dict['vm info']['network_type'] == 'vxlan':
        phy_port = dhcp_dict['vm info']['tunnel_port']
    vif_names["local nic:" + phy_port] = phy_port

    filter = "udp port (67 or 68) and ether host %s" % src_mac
    vxlan_filter = "(src %s or dst %s) and udp port (4789)" % (dhcp_dict['vm info']['tunnel_ip'], dhcp_dict['vm info']['tunnel_ip'])
    #vxlan_filter = "src %s" % dhcp_dict['vm info']['tunnel_ip']

    listeners = []
    for k,v in vif_names.items():
        if "local nic" in k and dhcp_dict['vm info']['network_type'] == 'vxlan':
            listeners.append(pcap.setup_listener(v, vxlan_filter))
        else:
            listeners.append(pcap.setup_listener(v, filter))

    threads = []
    for local_port in dhcp_dict['dhcp local host']:
        port_id = local_port['port_id'][:PORT_ID_PREFEX]
        t_thread = dhcp_port.create_pcap_file(port_id, dhcp_dict['vm info']['network_id'], dhcp_dict['vm info']['mac_address'], timeout=4)
	threads.append(t_thread)

    time.sleep(2)
    inject_packets(scapy, vif_names, src_mac)

    for thread in threads:
	thread.join()

    if dhcp_dict['vm info']['network_type'] == 'vlan':
        data = set_listeners.get_sniff_result(listeners, scapy.get_dhcp_mt, "local host")
    elif dhcp_dict['vm info']['network_type'] == 'vxlan':
        data = set_listeners.get_sniff_vxlan_result(src_mac, phy_port, listeners, scapy.get_dhcp_mt, "local host", dhcp_dict['vm info']['checker_type'])

    dhcp_port_data = []
    for local_port in dhcp_dict['dhcp local host']:
        port_id = local_port['port_id'][:PORT_ID_PREFEX]
        dhcp_port_data.append(dhcp_port.get_port_data(port_id, "local host dhcp server:"))

    for port in dhcp_port_data:
        data.update(port)

    return data

def inject_packets(scapy, vif_names, src_mac):
    scapy.send_dhcp_over_qbr(vif_names['qbr'], src_mac)
    time.sleep(3)
