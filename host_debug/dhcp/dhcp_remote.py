import sys
sys.path.append('../common/')
sys.path.append('../')

import dhcp_port
import discovery
import phy_int
import pcap_driver
import scapy_driver
import set_listeners
import time

VIF_PREFIX_LEN = 14
DEV_NAME_LEN = 14
PORT_ID_PREFEX = 11
QVB_DEV_PREFIX = "qvo"
DHCP_MESSATE_TYPE = ['', 'DHCPDISCOVER', 'DHCPOFFER', 'DHCPREQUEST',
                              'DHCPDECLINE', 'DHCPACK', 'DHCPNAK', 'DHCPRELEASE']
DHCP_NS_PREFIX = 'qdhcp-'
ARP_OP_TYPE = ['', 'REQUEST', 'REPLY']

class DHCPRemote:

    def __init__(self, dhcp_dict):
        self.dhcp_dict = dhcp_dict
        self.scapy = scapy_driver.ScapyDriver()


    def init_dhcp_check(self):
        pcap = pcap_driver.PcapDriver()

        vif_names = {}
        src_mac = self.dhcp_dict['src_mac_address']

        if self.dhcp_dict['network_type'] == 'vlan':
            phy_port = phy_int.get_phy_interface(self.dhcp_dict['bridge_name'])
        elif self.dhcp_dict['network_type'] == 'vxlan':
            phy_port = self.dhcp_dict['tunnel_port']
        vif_names["remote nic:" + phy_port] = phy_port

        filter = "udp port (67 or 68) and ether host %s" % src_mac
        vxlan_filter = "(src %s or dst %s) and udp port (4789)" % (self.dhcp_dict['tunnel_ip'], self.dhcp_dict['tunnel_ip'])

        listeners = []
        for k,v in vif_names.items():
            if "remote nic" in k and self.dhcp_dict['network_type'] == 'vxlan':
                listeners.append(pcap.setup_listener(v, vxlan_filter))
            else:
                listeners.append(pcap.setup_listener(v, filter))

        port_id = self.dhcp_dict['port_id'][:PORT_ID_PREFEX]
        t_thread = dhcp_port.create_pcap_file(port_id, self.dhcp_dict['network_id'], self.dhcp_dict['src_mac_address'], timeout=7)

        self.listeners = listeners
        self.t_thread = t_thread
        self.phy_port = phy_port
        self.src_mac = src_mac

    def collect_data(self):
        self.t_thread.join()
        if self.dhcp_dict['network_type'] == 'vlan':
            dhcp_remote_data = set_listeners.get_sniff_result(self.listeners, self.scapy.get_dhcp_mt, "remote host")
        elif self.dhcp_dict['network_type'] == 'vxlan':
            dhcp_remote_data = set_listeners.get_sniff_vxlan_result(self.src_mac, self.phy_port, self.listeners, self.scapy.get_dhcp_mt, "remote host", self.dhcp_dict['checker_type'])
        dhcp_remote_data = dhcp_port.merge_data(dhcp_remote_data, self.dhcp_dict)
	return dhcp_remote_data
