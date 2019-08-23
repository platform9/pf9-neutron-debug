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

        if self.listener_dict['checker_type'] == "ICMP":
            if not self.listener_dict['same_host']:
                vif_names.append({phy_port: {'is_ns':"None", 'port_type':"nic", 'filter': self.listener_dict['nic_filter']}})
        else:
            vif_names.append({phy_port: {'is_ns':"None", 'port_type':"nic", 'filter': self.listener_dict['nic_filter']}})


        if "bridge_name_remote_ext" in self.listener_dict:
           ext_phy_port = phy_interface.get_phy_interface(self.listener_dict['bridge_name_remote_ext'])
           vif_names.append({ext_phy_port: {'is_ns':"None", 'port_type':"ext_nic", 'filter': self.listener_dict['ext_nic_filter']}})

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
        if self.listener_dict['packet_type'] == "ICMP":
            if self.listener_dict['network_type'] == "vxlan":
                data = get_sniff_vxlan_result(self.phy_port, self.listeners, self.scapy.get_icmp_mt, self.listener_dict)
            else:
                data = get_sniff_result(self.listeners, self.scapy.get_icmp_mt)
        elif self.listener_dict['packet_type'] == "ARP":
            data = get_sniff_vxlan_result(self.phy_port, self.listeners, self.scapy.get_arp_op, self.listener_dict)
        elif self.listener_dict['packet_type'] == "DHCP":
            if self.listener_dict['network_type'] == "vxlan":
                data = get_sniff_vxlan_result(self.phy_port, self.listeners, self.scapy.get_dhcp_mt, self.listener_dict)
            else:
                data = get_sniff_result(self.listeners, self.scapy.get_dhcp_mt)
        return data


def get_sniff_result(listeners, handler):
    data = dict()
    for listener in listeners:
        vif_pre = listener.name
        data[vif_pre] = []
        for packet in listener.readpkts():
            packet_type, src, dst = handler(scapy.Ether(packet[1]))
            if packet_type is not None:
               data[vif_pre].append([packet_type, "src: %s" % src, "dst: %s" % dst])
    return data

def get_sniff_vxlan_result(phy_port, listeners, handler, listener_dict):
    data = dict()
    for listener in listeners:
        vif_pre = listener.name
        data[vif_pre] = []
        for packet in listener.readpkts():
            if listener.name == phy_port:
                outer_ether = scapy.Ether(packet[1])
                inner_ether = outer_ether[scapy.VXLAN]
                src_mac_address = listener_dict['src_mac_address']
                if listener_dict['checker_type'] == "SNAT":
                    src_ip_address = listener_dict['src_ip_address']
                    if listener_dict['packet_type'] in inner_ether and (inner_ether[scapy.IP].src == src_ip_address or inner_ether[scapy.IP].dst == src_ip_address):
                        packet_type, src, dst = handler(inner_ether)
                        if packet_type is not None:
                            data[vif_pre].append([packet_type, "src: %s" % src, "dst: %s" % dst])
                else:
                    if listener_dict['packet_type'] in inner_ether and (inner_ether.src == src_mac_address or inner_ether.dst == src_mac_address):
                        packet_type, src, dst = handler(inner_ether)
                        if packet_type is not None:
                            if "ARP" in listener_dict['tag']:
                                data[vif_pre].append([packet_type, "src: %s" % src, "dst: %s" % dst, outer_ether[scapy.IP].dst])
                            else:
                                data[vif_pre].append([packet_type, "src: %s" % src, "dst: %s" % dst])
            else:
                packet_type, src, dst = handler(scapy.Ether(packet[1]))
                if packet_type is not None:
                   data[vif_pre].append([packet_type, "src: %s" % src, "dst: %s" % dst])
    return data
