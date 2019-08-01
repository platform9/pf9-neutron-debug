import sys
sys.path.append('../../common/')

import pdb
import os
import init_neutron_client
import discovery

PORT_ID_PREFEX = 11

class ARPInfo:

    def __init__(self, vm_name, neutron):
        self.neutron = neutron

        self.vm_name = discovery.vmname_parse(vm_name)

        self.source_port_dict = discovery.get_port_dict(self.vm_name, self.neutron)

        self.network_id = self.source_port_dict['network_id']
        self.source_host_id = self.source_port_dict['binding:host_id']
        self.network_label = discovery.get_network_label(self.network_id, self.neutron)
        self.network_type = discovery.get_network_type(self.network_id, self.neutron)

        if self.network_type == "vlan":
            self.source_arp_listen_dict = {'network_type':"vlan"}
	    self.inject_arp_dict = {}
        else:
            self.format_arp_dicts()

    def format_arp_dicts(self):

        self.source_arp_listen_dict = self.format_source_dict()
        self.inject_arp_dict = self.format_inject_dict()

    def format_source_dict(self):
        source_arp_dict = dict()
        source_arp_dict['checker_type'] = "ARP"
        source_arp_dict['vm_name'] = self.vm_name
        source_arp_dict['src_ip_address'] = self.source_port_dict['fixed_ips'][0]['ip_address']
        source_arp_dict['src_mac_address'] = self.source_port_dict['mac_address']
	source_arp_dict['dest_ip_address'] = discovery.get_start_ip(self.network_id, self.neutron)
        source_arp_dict['host_id'] = self.source_host_id
        source_arp_dict['port_id'] = self.source_port_dict['id']
        source_arp_dict['network_label'] = self.network_label
        source_arp_dict['network_type'] = self.network_type
        source_arp_dict['filter'] = ""
        source_arp_dict['bridge_name'] = discovery.get_bridge_name(self.network_label, self.source_host_id, self.neutron)
        source_arp_dict['tag'] = "arp_source"
        source_arp_dict['vif_names'] = []

        tunnel_ip = discovery.get_tunnel_ip(self.source_host_id, self.neutron)
        source_arp_dict['tunnel_ip'] = tunnel_ip
        source_arp_dict['vxlan_filter'] = "src %s and udp port (4789)" % (source_arp_dict['tunnel_ip'])
        source_arp_dict['tunnel_port'] = discovery.get_tunnel_port(self.source_host_id, source_arp_dict['tunnel_ip'], self.neutron)

        return source_arp_dict

    def format_inject_dict(self):

        inject_arp_dict = dict()
        inject_arp_dict.update(self.source_arp_listen_dict)
        inject_arp_dict['payload'] = "abcd" * 3
        inject_arp_dict['inject_port'] = "qbr" + self.source_arp_listen_dict['port_id'][:PORT_ID_PREFEX]

        return inject_arp_dict


    def get_source_arp_dict(self):
        return self.source_arp_listen_dict

    def get_inject_arp_dict(self):
        return self.inject_arp_dict
