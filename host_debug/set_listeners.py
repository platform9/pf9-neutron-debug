import sys
sys.path.append('../common/')

import discovery
import phy_interface
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

        if self.listener_dict['network_type'] == "vxlan":
            phy_port = self.listener_dict['tunnel_port']
        else:
            phy_port = phy_interface.get_phy_interface(self.listener_dict['bridge_name'])

        vif_names.append({phy_port: {'is_ns':"None", 'port_type':"nic", 'filter': self.listener_dict['nic_filter']}})

	
	if "bridge_name_remote_ext" in self.listener_dict:
	   ext_phy_port = phy_interface.get_phy_interface(self.listener_dict['bridge_name_remote_ext'])
	   vif_names.append({ext_phy_port: {'is_ns':"None", 'port_type':"ext_nic", 'filter': self.listener_dict['ext_nic_filter']}})
	   print vif_names

        listeners = []
        for vif in vif_names:
	    for vif_name, vif_dict in vif.items():
                if "nic" == vif_dict["port_type"] and self.listener_dict['network_type'] == 'vxlan':
                   listeners.append(pcap.setup_listener(vif_name, self.listener_dict['vxlan_filter']))
                elif "nic" == vif_dict["port_type"]:
                   listeners.append(pcap.setup_listener(vif_name, self.listener_dict['nic_filter']))
		elif "ext_nic" == vif_dict["port_type"]:
		   listeners.append(pcap.setup_listener(vif_name, self.listener_dict['ext_nic_filter']))
                else:
                   listeners.append(pcap.setup_listener(vif_name, vif_dict['filter']))

        self.listeners = listeners
        self.phy_port = phy_port

        return listeners

    def collect_data(self):
        if self.listener_dict['checker_type'] == "ICMP" or self.listener_dict['checker_type'] == "FIP" or self.listener_dict['checker_type'] == "SNAT":
            if self.listener_dict['network_type'] == "vxlan":
                data = get_sniff_vxlan_result(self.listener_dict['src_mac_address'], self.phy_port, self.listeners, self.scapy.get_icmp_mt, self.listener_dict['tag'], self.listener_dict['checker_type'])
            else:
                data = get_sniff_result(self.listeners, self.scapy.get_icmp_mt, self.listener_dict['tag'])
        elif self.listener_dict['checker_type'] == "ARP":
            data = get_sniff_vxlan_result(self.listener_dict['src_mac_address'], self.phy_port, self.listeners, self.scapy.get_arp_op, self.listener_dict['tag'], self.listener_dict['checker_type'])
        return data


def get_sniff_result(listeners, handler, tag):
    data = dict()
    for listener in listeners:
        vif_pre = listener.name
        data[tag + ":" + vif_pre] = []
        for packet in listener.readpkts():
            packet_type, src, dst = handler(str(packet[1]))
            if packet_type is not None:
               data[tag + ":" + vif_pre].append([packet_type, "src: %s" % src, "dst: %s" % dst])
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
                    packet_type, src, dst = handler(str(inner_packet))
                    if packet_type is not None:
                        if "arp" in tag:
                            data[tag + ":" + vif_pre].append([packet_type, "src: %s" % src, "dst: %s" % dst, outer_ether[scapy.IP].dst])
                        else:
                            data[tag + ":" + vif_pre].append([packet_type, "src: %s" % src, "dst: %s" % dst])
            else:
                packet_type, src, dst = handler(str(packet[1]))
                if packet_type is not None:
                   data[tag + ":" + vif_pre].append([packet_type, "src: %s" % src, "dst: %s" % dst])
    return data
