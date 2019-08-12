import os
import pcap
import scapy_driver
import threading
from scapy import all as scapy

PORT_ID_PREFEX = 11
DHCP_MESSATE_TYPE = ['', 'DHCPDISCOVER', 'DHCPOFFER', 'DHCPREQUEST',
                              'DHCPDECLINE', 'DHCPACK', 'DHCPNAK', 'DHCPRELEASE']
ICMP_MESSAGE_TYPE = {0:'REPLY',8:'REQUEST', 3:'DEST_UNREACHABLE'}
TIMEOUT = 7

class SetNsListener:

    def __init__(self, listener_dict):
        self.listener_dict = listener_dict
        self.scapy_dr = scapy_driver.ScapyDriver()
        self.threads = []

    def init_listeners(self):
        for vif in self.listener_dict['ns_vif_names']:
            for vif_name, vif_dict in vif.items():
                self.threads.append(self.create_pcap_file(vif_dict['is_ns'], vif_name, vif_dict['filter']))

    def create_pcap_file(self, ns, vif_name, filter):
        tcp_thread = threading.Thread(target=tcpdump_process,args=(ns, vif_name, filter,))
        tcp_thread.start()
        return tcp_thread

    def join_threads(self):
	for thread in self.threads:
	   thread.join()

    def collect_data(self):

        data = dict()
        tag = self.listener_dict['tag']

	self.join_threads()

        for vif in self.listener_dict['ns_vif_names']:
            for vif_name, vif_dict in vif.items():
                packets = scapy.rdpcap("../pcap/%s.pcap" % vif_name)

                data[tag + ":" + vif_name] = []
                for p in packets:
                    if self.listener_dict['checker_type'] == "FIP" or self.listener_dict['checker_type'] == "SNAT":
                        packet_type, src, dst = p[scapy.ICMP].type, p.src, p.dst
			if packet_type in ICMP_MESSAGE_TYPE:
			   message_type = ICMP_MESSAGE_TYPE[packet_type]
                    if message_type is not None:
                       data[tag + ":" + vif_name].append([message_type, "src: %s" % src, "dst: %s" % dst])
        return data


def tcpdump_process(ns, vif, filter):
    os.system('ip netns exec %s timeout %d tcpdump -l -evvvnn -i %s %s -w "../pcap/%s.pcap"' % (ns, TIMEOUT, vif, filter, vif))
