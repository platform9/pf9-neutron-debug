import sys

import pdb
import os
from debug.common import init_neutron_client
from debug.common import discovery

DHCP_OWNER = 'network:dhcp'
VIF_PREFIX_LEN = 14

class DHCPInfo:
    """
    Uses OpenStack SDK to retrieve all relevant information about a VM and the network it is on, for the DHCP Checker
    """

    def __init__(self, vm_name, neutron):

        self.neutron = neutron
        self.vm_name = discovery.vmname_parse(vm_name)

        self.source_port_dict = discovery.get_port_dict(self.vm_name, self.neutron)
        self.network_id = self.source_port_dict['network_id']
        self.source_host_id = self.source_port_dict['binding:host_id']
        self.dhcp_ports = discovery.get_all_dhcp_ports(self.network_id, self.neutron)

        self.network_label = discovery.get_network_label(self.network_id, self.neutron)
        self.network_type = discovery.get_network_type(self.network_id, self.neutron)

        self.local_dhcp = self.is_local_dhcp()

        self.vif_names = self.get_vif_list()
        self.vm_dict = self.format_vm_dict()
        self.dhcp_list = self.format_dhcp_dicts()
        self.inject_dict = self.format_inject_dict()

    def format_vm_dict(self):

        bridge_name = discovery.get_bridge_name(self.network_label, self.source_port_dict['binding:host_id'], self.neutron)
        tunnel_ip = discovery.get_tunnel_ip(self.source_port_dict['binding:host_id'], self.neutron)

        vm_dict = dict()
        vm_dict['vm_name'] = self.vm_name
        vm_dict['checker_type'] = "DHCP"
        vm_dict['packet_type'] = "DHCP"
        vm_dict['src_mac_address'] = self.source_port_dict['mac_address']
        vm_dict['port_id'] = self.source_port_dict['id']
        vm_dict['device_id'] = self.source_port_dict['device_id']
        vm_dict['host_id'] = self.source_port_dict['binding:host_id']
        vm_dict['network_id'] = self.network_id
        vm_dict['network_type'] = self.network_type
        vm_dict['network_label'] = self.network_label
        vm_dict['ip_address'] = self.source_port_dict['fixed_ips'][0]['ip_address']
        vm_dict['nic_filter'] = "udp port (67 or 68) and ether host %s" % vm_dict['src_mac_address']
        vm_dict['vxlan_filter'] = "(src %s or dst %s) and udp port (4789)" % (tunnel_ip, tunnel_ip)
        vm_dict['tunnel_ip'] = tunnel_ip
        vm_dict['tag'] = "VM SOURCE"
        vm_dict['bridge_name'] = bridge_name
        vm_dict["num_dhcp"] = len(self.dhcp_ports)
        vm_dict["local_dhcp"] = self.local_dhcp
        vm_dict['vif_names'] = self.vif_names


        if self.network_type == "vxlan":
            vm_dict['tunnel_port'] = discovery.get_tunnel_port(vm_dict['host_id'], tunnel_ip, self.neutron)
        else:
            vm_dict['tunnel_port'] = "None"

        return vm_dict

    def format_dhcp_dicts(self):

        dhcp_list = []
        for dhcp_port in self.dhcp_ports:
            dhcp_dict = dict()
            dhcp_host_id = dhcp_port['binding:host_id']
            dhcp_bridge_name = discovery.get_bridge_name(self.network_label, dhcp_host_id, self.neutron)
            dhcp_tunnel_ip = discovery.get_tunnel_ip(dhcp_host_id, self.neutron)
            if self.network_type == "vxlan":
                dhcp_tunnel_port = discovery.get_tunnel_port(dhcp_host_id, dhcp_tunnel_ip, self.neutron)
            else:
                dhcp_tunnel_port = "None"

            dhcp_dict = {'port_id':dhcp_port['id'], 'network_label':self.network_label, 'network_type':self.network_type, 'network_id':self.network_id, 'bridge_name':dhcp_bridge_name,
                         'host_id': dhcp_host_id, 'src_mac_address':self.source_port_dict['mac_address'], 'tunnel_ip':dhcp_tunnel_ip, 'nic_filter':"udp port (67 or 68) and ether host %s" % self.source_port_dict['mac_address'],
			 'vxlan_filter': "(src %s or dst %s) and udp port (4789)" % (dhcp_tunnel_ip, dhcp_tunnel_ip),'tunnel_port':dhcp_tunnel_port, 'checker_type':"DHCP", 'packet_type':"DHCP", 'tag':"DHCP_NS"}

            full_name = "tap" + dhcp_dict['port_id']
            dhcp_tap_device = full_name[:VIF_PREFIX_LEN]
            dhcp_ns = "qdhcp-" + self.network_id

            ns_vif_list = []
            vif = dict()
            vif[dhcp_tap_device] = {'filter':"udp port 67 or 68 and ether host %s" % dhcp_dict['src_mac_address'], 'is_ns':dhcp_ns, 'port_type':dhcp_tap_device}
            ns_vif_list.append(vif)

            dhcp_dict['ns_vif_names'] = ns_vif_list
            dhcp_dict['vif_names'] = []
            dhcp_list.append(dhcp_dict)

        return dhcp_list

    def format_inject_dict(self):

        inject_dict = dict()
        inject_dict.update(self.vm_dict)

        for vif in inject_dict['vif_names']:
            if "qbr" in list(vif.keys())[0]:
               inject_port = list(vif.keys())[0]
               break

        inject_dict['inject_port'] = inject_port
        return inject_dict

    def is_local_dhcp(self):

        for dhcp_port in self.dhcp_ports:
            if dhcp_port['binding:host_id'] == self.source_host_id:
                return True
        return False


    def get_vm_dict(self):
        return self.vm_dict

    def get_dhcp_list(self):
        return self.dhcp_list

    def get_inject_dict(self):
        return self.inject_dict

    def get_vif_list(self):

        vif_list = []
        vif_names = discovery.get_vif_names(self.source_port_dict['id'])
        for port_type, vif_name in vif_names.items():
            vif = dict()
            vif[vif_name] = dict()
            vif[vif_name]['filter'] = "udp port (67 or 68) and ether host %s" % self.source_port_dict['mac_address']
            vif[vif_name]['is_ns'] = "None"
            vif[vif_name]['port_type'] = port_type
            vif_list.append(vif)

        return vif_list
