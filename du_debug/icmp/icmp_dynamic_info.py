import sys
sys.path.append('../../common/')

import pdb
import os
import init_neutron_client
import discovery

class ICMPInfo:

    def __init__(self, source_vm, dest_vm, neutron):
        self.neutron = neutron

        self.source_vm = discovery.vmname_parse(source_vm)
        self.dest_vm = discovery.vmname_parse(dest_vm)

        self.source_port_dict = discovery.get_port_dict(self.source_vm, self.neutron)
        self.dest_port_dict = discovery.get_port_dict(self.dest_vm, self.neutron)

        self.network_id = self.source_port_dict['network_id']
        self.source_host_id = self.source_port_dict['binding:host_id']
        self.dest_host_id = self.dest_port_dict['binding:host_id']
        self.network_label = discovery.get_network_label(self.network_id, self.neutron)
        self.network_type = discovery.get_network_type(self.network_id, self.neutron)

        self.format_icmp_dicts()



    def format_icmp_dicts(self):

        self.source_icmp_listen_dict = self.format_source_dict()
        self.dest_icmp_listen_dict = self.format_dest_dict()
        self.inject_icmp_dict = self.format_inject_dict()

    def format_source_dict(self):
        source_icmp_dict = dict()
        source_icmp_dict['checker_type'] == "ICMP"
        source_icmp_dict['vm_name'] = self.source_vm
        source_icmp_dict['src_ip_address'] = self.source_port_dict['fixed_ips'][0]['ip_address']
        source_icmp_dict['src_mac_address'] = self.source_port_dict['mac_address']
        source_icmp_dict['dest_ip_address'] = self.dest_port_dict['fixed_ips'][0]['ip_address']
        source_icmp_dict['dest_mac_address'] = self.dest_port_dict['mac_address']
        source_icmp_dict['host_id'] = self.source_host_id
        source_icmp_dict['port_id'] = self.source_port_dict['id']
        source_icmp_dict['network_label'] = self.network_label
        source_icmp_dict['network_type'] = self.network_type
        source_icmp_dict['filter'] = "icmp and ((src %s and dst %s) or (src %s and dst %s)) "
        source_icmp_dict['bridge_name'] = discovery.get_bridge_name(self.network_label, self.source_host_id, self.neutron)
        source_icmp_dict['tag'] = "source"
        source_icmp_dict['vif_names'] = []

        tunnel_ip = discovery.get_tunnel_ip(self.source_host_id, self.neutron)
        source_icmp_dict['tunnel_ip'] = tunnel_ip
        source_icmp_dict['vxlan_filter'] = "(src %s or dst %s) and udp port (4789)" % (source_icmp_dict['tunnel_ip'], source_icmp_dict['tunnel_ip'])

        if source_icmp_dict['network_type'] == "vxlan":
            source_icmp_dict['tunnel_port'] = discovery.get_tunnel_port(self.source_host_id, source_icmp_dict['tunnel_ip'], self.neutron)
        else:
            source_icmp_dict['tunnel_port'] = "None"

        vif_names = discovery.get_vif_names(source_icmp_dict['port_id'])
        for port_type, vif_name in vif_names.items():
            vif = dict()
            vif[vif_name] = dict()
            vif[vif_name]['filter'] = "icmp and ((src %s and dst %s) or (src %s and dst %s)) "
            vif[vif_name]['is_ns'] = "None"
	    vif[vif_name]['port_type'] = port_type
            source_icmp_dict['vif_names'].append(vif)

        return source_icmp_dict

    def format_dest_dict(self):

        dest_icmp_dict = dict()
        dest_icmp_dict['checker type'] = "ICMP"
        dest_icmp_dict['vm_name'] = self.dest_vm
        dest_icmp_dict['src_ip_address'] = self.source_port_dict['fixed_ips'][0]['ip_address']
        dest_icmp_dict['src_mac_address'] = self.source_port_dict['mac_address']
        dest_icmp_dict['dest_ip_address'] = self.dest_port_dict['fixed_ips'][0]['ip_address']
        dest_icmp_dict['dest_mac_address'] = self.dest_port_dict['mac_address']
        dest_icmp_dict['host_id'] = self.dest_host_id
        dest_icmp_dict['port_id'] = self.dest_port_dict['id']
        dest_icmp_dict['network_label'] = self.network_label
        dest_icmp_dict['network_type'] = self.network_type
        dest_icmp_dict['filter'] = "icmp and ((src %s and dst %s) or (src %s and dst %s)) "
        dest_icmp_dict['bridge_name'] = discovery.get_bridge_name(self.network_label, self.dest_host_id, self.neutron)
        dest_icmp_dict['tag'] = "destination"
        dest_icmp_dict['vif_names'] = []

        tunnel_ip = discovery.get_tunnel_ip(self.dest_host_id, self.neutron)
        dest_icmp_dict['tunnel_ip'] = tunnel_ip
        dest_icmp_dict['vxlan_filter'] = "(src %s or dst %s) and udp port (4789)" % (dest_icmp_dict['tunnel_ip'], dest_icmp_dict['tunnel_ip'])

        if dest_icmp_dict['network_type'] == "vxlan":
            dest_icmp_dict['tunnel_port'] = discovery.get_tunnel_port(self.dest_host_id, dest_icmp_dict['tunnel_ip'], self.neutron)
        else:
            dest_icmp_dict['tunnel_port'] = "None"

        vif_names = discovery.get_vif_names(dest_icmp_dict['port_id'])
        for port_type, vif_name in vif_names.items():
            vif = dict()
            vif[vif_name] = dict()
            vif[vif_name]['filter'] = "icmp and ((src %s and dst %s) or (src %s and dst %s)) "
            vif[vif_name]['is_ns'] = "None"
	    vif[vif_name]['port_type'] = port_type
            dest_icmp_dict['vif_names'].append(vif)

        return dest_icmp_dict

    def format_inject_dict(self):

        inject_icmp_dict = dict()
        inject_icmp_dict.update(self.source_icmp_listen_dict)
        inject_icmp_dict['payload'] = "abcd" * 3

	for vif in inject_icmp_dict['vif_names']:
	    if "qbr" in vif.keys()[0]:
		inject_port = vif.keys()[0]
		break

        inject_icmp_dict['inject_port'] = inject_port

        return inject_icmp_dict


    def get_source_icmp_dict(self):
        return self.source_icmp_listen_dict

    def get_dest_icmp_dict(self):
        return self.dest_icmp_listen_dict

    def get_inject_icmp_dict(self):
        return self.inject_icmp_dict
