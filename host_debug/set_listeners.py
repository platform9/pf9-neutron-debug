import sys
sys.path.append('../common/')

import discovery
import phy_int
import pcap_driver
import scapy_driver
import time

def init_listeners(listener_dict):
    pcap = pcap_driver.PcapDriver()

    vif_names = listener_dict['vif names']

    phy_port = phy_int.get_phy_interface(listener_dict['bridge_name'])
    vif_names["source nic:" + phy_port] = phy_port

    filter = listener_dict['filter'] % (listener_dict['src_mac_address'], listener_dict['dest_ip_address'], listener_dict['dest_ip_address'], listener_dict['src_mac_address'])

    listeners = []
    for k,v in vif_names.items():
        listeners.append(pcap.setup_listener(v, filter))

    return listeners

def get_sniff_result(listeners, handler, tag):
    data = dict()
    for listener in listeners:
        vif_pre = listener.name
        data[tag + vif_pre] = []
        for packet in listener.readpkts():
            icmp_type = handler(str(packet[1]))
            if icmp_type is not None:
               data[tag + vif_pre].append(icmp_type)
    return data