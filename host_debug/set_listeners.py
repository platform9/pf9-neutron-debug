import sys
sys.path.append('../common/')

import discovery
import phy_int
import pcap_driver
import scapy_driver
import time

import pcap
from scapy import all as scapy

class SetListener:

    def __init__(self, listener_dict):
        self.listener_dict = listener_dict
        self.scapy = scapy_driver.ScapyDriver()

    def init_listeners(self):
        pcap = pcap_driver.PcapDriver()

        vif_names = self.listener_dict['vif_names']
        vif_names = self.vif_list_to_dict(vif_names)

        if self.listener_dict['network_type'] == "vxlan":
            phy_port = self.listener_dict['tunnel_port']
        else:
            phy_port = phy_int.get_phy_interface(self.listener_dict['bridge_name'])
        vif_names["nic:" + phy_port] = phy_port

        filter = self.listener_dict['filter'] % (self.listener_dict['src_ip_address'], self.listener_dict['dest_ip_address'], self.listener_dict['dest_ip_address'], self.listener_dict['src_ip_address'])

        listeners = []
        for k,v in vif_names.items():
            if "nic" in k and self.listener_dict['network_type'] == 'vxlan':
                listeners.append(pcap.setup_listener(v, self.listener_dict['vxlan_filter']))
            else:
                listeners.append(pcap.setup_listener(v, filter))

        self.listeners = listeners
        self.phy_port = phy_port

        return listeners

    def vif_list_to_dict(self, vif_names):

        vif_dict = dict()

        for vif in vif_names:
    	vif_dict[vif[vif.keys()[0]]['port_type']] = vif.keys()[0]

        return vif_dict

    def collect_data(self):
        if self.listener_dict['checker_type'] == "ICMP":
            if self.listener_dict['network_type'] == "vlan":
                icmp_data = get_sniff_result(self.listeners, self.scapy.get_icmp_mt, self.listener_dict['tag'])
            elif self.listener_dict['network_type'] == "vxlan":
                icmp_data = get_sniff_vxlan_result(self.listener_dict['src_mac_address'], self.phy_port, self.listeners, self.scapy.get_icmp_mt, self.listener_dict['tag'], self.listener_dict['checker_type'])
        return icmp_data


def get_sniff_result(listeners, handler, tag):
    data = dict()
    for listener in listeners:
        vif_pre = listener.name
        data[tag + ":" + vif_pre] = []
        for packet in listener.readpkts():
            icmp_type, src, dst = handler(str(packet[1]))
            if icmp_type is not None:
               data[tag + ":" + vif_pre].append([icmp_type, "src: %s" % src, "dst: %s" % dst])
    return data

def get_sniff_vxlan_result(src_mac, phy_port,listeners, handler, tag, checker_type):
    data = dict()
    for listener in listeners:
        vif_pre = listener.name
        data[tag + ":" + vif_pre] = []
        for packet in listener.readpkts():
            if listener.name == phy_port:
            	outer_ether = scapy.Ether(packet[1])
            	inner_packet = outer_ether.load
            	inner_ether = scapy.Ether(inner_packet)
                if (inner_ether.src == src_mac or inner_ether.dst == src_mac) and checker_type in inner_ether:
                    icmp_type, src, dst = handler(str(inner_packet))
                    if icmp_type is not None:
                        data[tag + ":" + vif_pre].append([icmp_type, "src: %s" % src, "dst: %s" % dst])
            else:
                icmp_type, src, dst = handler(str(packet[1]))
                if icmp_type is not None:
                   data[tag + ":" + vif_pre].append([icmp_type, "src: %s" % src, "dst: %s" % dst])
    return data
