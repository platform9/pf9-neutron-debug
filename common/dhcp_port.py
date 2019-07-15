import os
import pcap
import scapy_driver
import threading
from scapy import all as scapy

DHCP_MESSATE_TYPE = ['', 'DHCPDISCOVER', 'DHCPOFFER', 'DHCPREQUEST',
                              'DHCPDECLINE', 'DHCPACK', 'DHCPNAK', 'DHCPRELEASE']

def create_pcap_file(port_id, network_id, mac_address):
    dhcp_namespace = "qdhcp-" + network_id
    vif = "tap" + port_id
    tcp_thread = threading.Thread(target=tcpdump_process,args=(dhcp_namespace, vif, mac_address,))
    tcp_thread.start()
    return tcp_thread

def tcpdump_process(dhcp_ns, vif, mac):
    os.system('ip netns exec %s timeout 4 tcpdump -l -evvvnn -i %s udp port 67 or 68 and ether host %s -w "../pcap/%s.pcap"' % (dhcp_ns, vif, mac, vif))
    

def get_port_data(port_id, flag):
    vif  = "tap" + port_id
    packets = scapy.rdpcap("../pcap/%s.pcap" % vif)

    data = dict()
    data[flag + vif] = []

    for p in packets:
        packet = str(p)
        dhcp_packet = p[scapy.DHCP]
        message = dhcp_packet.options[0]
        icmp_type = DHCP_MESSATE_TYPE[message[1]]
        if icmp_type is not None:
               data[flag + vif].append(icmp_type)

    return data
