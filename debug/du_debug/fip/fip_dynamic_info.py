import sys

import pdb
import os
from debug.common import init_neutron_client
from debug.common import discovery

PORT_ID_PREFEX = 10

class FIPInfo:
    """
    Uses OpenStack SDK to retrieve all relevant information about a VM and the network it is on, for the FIP Checker
    """

    def __init__(self, vm_name, neutron):
        self.neutron = neutron

        self.vm_name = discovery.vmname_parse(vm_name)
        self.source_port_dict = discovery.get_port_dict(self.vm_name, self.neutron)
        self.fixed_ip_address = self.source_port_dict['fixed_ips'][0]['ip_address']
        self.network_id = self.source_port_dict['network_id']
        self.router_id, self.floating_network_id, self.floating_ip = discovery.get_fip_info(self.fixed_ip_address, self.neutron)
        self.source_host_id = self.source_port_dict['binding:host_id']
        self.network_label = discovery.get_network_label(self.floating_network_id, self.neutron)
        self.network_type = discovery.get_network_type(self.floating_network_id, self.neutron)

        self.format_fip_dicts()


    def format_fip_dicts(self):

        self.listen_fip_dict = self.format_listen_dict()
        self.inject_fip_dict = self.format_inject_dict()

    def format_listen_dict(self):

        listen_fip_dict = dict()
        listen_fip_dict['checker_type'] = "FIP"
        listen_fip_dict['packet_type'] = "ICMP"
        listen_fip_dict['vm_name'] = self.vm_name
        listen_fip_dict['src_ip_address'] = self.source_port_dict['fixed_ips'][0]['ip_address']
        listen_fip_dict['src_mac_address'] = self.source_port_dict['mac_address']
        listen_fip_dict['dest_ip_address'] = "8.8.8.8"
        listen_fip_dict['host_id'] = self.source_host_id
        listen_fip_dict['port_id'] = self.source_port_dict['id']
        listen_fip_dict['qr_port_id'], listen_fip_dict['dest_mac_address'] = discovery.get_qr_port(self.router_id, self.neutron)
        listen_fip_dict['fg_port_id'] = discovery.get_fg_port(self.floating_network_id, self.source_host_id, self.neutron)
        listen_fip_dict['network_label'] = self.network_label
        listen_fip_dict['network_type'] = self.network_type
        listen_fip_dict['nic_filter'] = "icmp and  ((src %s and dst %s) or (src %s and dst %s)) " % (self.floating_ip, listen_fip_dict['dest_ip_address'], listen_fip_dict['dest_ip_address'], self.floating_ip)
        listen_fip_dict['bridge_name'] = discovery.get_bridge_name(self.network_label, self.source_host_id, self.neutron)
        listen_fip_dict['tag'] = "SOURCE VM"
        listen_fip_dict['vif_names'] = []
        listen_fip_dict['ns_vif_names'] = []
        listen_fip_dict["path_type"] = "bidirectional"

        vif_names = discovery.get_vif_names(listen_fip_dict['port_id'])
        for port_type, vif_name in vif_names.items():
            vif = dict()
            vif[vif_name] = dict()
            vif[vif_name]['filter'] = "icmp and ((src %s and dst %s) or (src %s and dst %s)) " % (listen_fip_dict['src_ip_address'], listen_fip_dict['dest_ip_address'], listen_fip_dict['dest_ip_address'], listen_fip_dict['src_ip_address'])
            vif[vif_name]['is_ns'] = "None"
            vif[vif_name]['port_type'] = port_type
            listen_fip_dict['vif_names'].append(vif)

        vif_names = discovery.get_fip_interfaces(self.router_id, self.floating_network_id, listen_fip_dict['qr_port_id'], listen_fip_dict['fg_port_id'])
        for vif_name, netns in vif_names.items():
            vif = dict()
            vif[vif_name] = dict()
            if "qr" in vif_name:
            	vif[vif_name]['filter'] = "icmp and host %s and host %s " % (listen_fip_dict['src_ip_address'], listen_fip_dict['dest_ip_address'])
            else:
                vif[vif_name]['filter'] = "icmp and host %s and host %s " % (self.floating_ip, listen_fip_dict['dest_ip_address'])
            vif[vif_name]['is_ns'] = netns
            vif[vif_name]['port_type'] = vif_name
            listen_fip_dict['ns_vif_names'].append(vif)
        return listen_fip_dict

    def format_inject_dict(self):

        inject_fip_dict = dict()
        inject_fip_dict.update(self.listen_fip_dict)
        inject_fip_dict['payload'] = "abcd" * 3

        for vif in inject_fip_dict['vif_names']:
            if "qbr" in list(vif.keys())[0]:
               inject_port = list(vif.keys())[0]
               break

        inject_fip_dict['inject_port'] = inject_port
        return inject_fip_dict

    def get_listen_fip_dict(self):
        return self.listen_fip_dict

    def get_inject_fip_dict(self):
        return self.inject_fip_dict
