import sys
sys.path.append('../common/')

import discovery
import phy_int
import pcap_driver
import scapy_driver
import time

import pcap
from scapy import all as scapy


def init_listeners(listener_dict):
    pcap = pcap_driver.PcapDriver()

    vif_names = listener_dict['vif_names']
    vif_names = vif_list_to_dict(vif_names)

    phy_port = phy_int.get_phy_interface(listener_dict['bridge_name'])
    vif_names["source nic:" + phy_port] = phy_port

    filter = listener_dict['filter'] % (listener_dict['src_ip_address'], listener_dict['dest_ip_address'], listener_dict['dest_ip_address'], listener_dict['src_ip_address'])

    listeners = []
    for k,v in vif_names.items():
        listeners.append(pcap.setup_listener(v, filter))

    return listeners

def vif_list_to_dict(vif_names):

    vif_dict = dict()

    for vif in vif_names:
	vif_dict[vif[vif.keys()[0]]['port_type']] = vif.keys()[0]

    return vif_dict

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

def get_sniff_vxlan_result(src_mac, phy_port,listeners, handler, tag):
    data = dict()
    for listener in listeners:
        vif_pre = listener.name
        data[tag + ":" + vif_pre] = []
        for packet in listener.readpkts():
            outer_ether = scapy.Ether(packet[1])
            inner_packet = outer_ether.load
            inner_ether = scapy.Ether(inner_packet)
            if listener.name == phy_port:
                if inner_ether.src == src_mac and "DHCP" in inner_ether:
                    icmp_type, src, dst = handler(str(inner_packet))
                    if icmp_type is not None:
                        data[tag + ":" + vif_pre].append([icmp_type, "src: %s" % src, "dst: %s" % dst])
            else:
                icmp_type, src, dst = handler(str(packet[1]))
                if icmp_type is not None:
                   data[tag + ":" + vif_pre].append([icmp_type, "src: %s" % src, "dst: %s" % dst])
    return data
