import sys
sys.path.append('../../common/')

import pdb
import os
import init_neutron_client
import discovery

PORT_ID_PREFEX = 10

class SNATInfo:
    """
    Uses OpenStack SDK to retrieve all relevant information about a VM and the network it is on, for the SNAT Checker
    """

    def __init__(self, vm_name, neutron):
        self.neutron = neutron

        self.vm_name = discovery.vmname_parse(vm_name)
        self.source_port_dict = discovery.get_port_dict(self.vm_name, self.neutron)
        self.source_host_id = self.source_port_dict['binding:host_id']
        self.fixed_ip_address = self.source_port_dict['fixed_ips'][0]['ip_address']
        self.tenant_network_id = self.source_port_dict['network_id']
        self.sg_port = discovery.get_sg_port(self.tenant_network_id, self.neutron)
        self.router_id = self.sg_port['device_id']
        self.qr_port_id, self.dest_mac_address = discovery.get_qr_port(self.router_id, self.neutron)
        self.qg_port = discovery.get_qg_port(self.router_id, self.neutron)
        self.external_network_id = self.qg_port['network_id']
        self.snat_external_ip = self.qg_port['fixed_ips'][0]['ip_address']
        self.dest_ip_address = "8.8.8.8"
        self.vif_names = self.get_vif_list()
        self.ns_vif_names = self.get_ns_vif_list()
        self.snat_host_id = self.sg_port['binding:host_id']

        snat_host = self.determine_snat_host()

        if snat_host == "local snat":
            self.local_listen_dict = self.init_local_snat_process()
            self.remote_listen_dict = {}
        else:
            self.local_listen_dict, self.remote_listen_dict = self.init_remote_snat_process()

        self.inject_icmp_dict = self.format_inject_dict()

    def init_local_snat_process(self):

        local_listen_dict = dict()
        local_listen_dict['checker_type'] = "SNAT"
        local_listen_dict['packet_type'] = "ICMP"
        local_listen_dict['vm_name'] = self.vm_name
        local_listen_dict['src_ip_address'] = self.fixed_ip_address
        local_listen_dict['src_mac_address'] = self.source_port_dict['mac_address']
        local_listen_dict['dest_ip_address'] = self.dest_ip_address
        local_listen_dict['dest_mac_address'] = self.dest_mac_address
        local_listen_dict['host_id'] = self.source_host_id
        local_listen_dict['port_id'] = self.source_port_dict['id']
        local_listen_dict['network_label'] = discovery.get_network_label(self.external_network_id, self.neutron)
        local_listen_dict['network_type'] = discovery.get_network_type(self.external_network_id, self.neutron)
        local_listen_dict['nic_filter'] = "icmp and  ((src %s and dst %s) or (src %s and dst %s)) " % (self.snat_external_ip, self.dest_ip_address, self.dest_ip_address, self.snat_external_ip)
        local_listen_dict['bridge_name'] = discovery.get_bridge_name(local_listen_dict['network_label'], self.source_host_id, self.neutron)
        local_listen_dict['tag'] = "VM SOURCE"
        local_listen_dict['vif_names'] = self.vif_names
        local_listen_dict['ns_vif_names'] = self.ns_vif_names
        local_listen_dict['snat_host'] = "local"

        return local_listen_dict

    def init_remote_snat_process(self):

        local_listen_dict = dict()
        local_listen_dict['checker_type'] = "SNAT"
        local_listen_dict['packet_type'] = "ICMP"
        local_listen_dict['vm_name'] = self.vm_name
        local_listen_dict['src_ip_address'] = self.fixed_ip_address
        local_listen_dict['src_mac_address'] = self.source_port_dict['mac_address']
        local_listen_dict['dest_ip_address'] = self.dest_ip_address
        local_listen_dict['dest_mac_address'] = self.dest_mac_address
        local_listen_dict['host_id'] = self.source_host_id
        local_listen_dict['port_id'] = self.source_port_dict['id']
        local_listen_dict['network_label'] = discovery.get_network_label(self.tenant_network_id, self.neutron)
        local_listen_dict['network_type'] = discovery.get_network_type(self.tenant_network_id, self.neutron)
        local_listen_dict['nic_filter'] = "icmp and  ((src %s and dst %s) or (src %s and dst %s)) " % (self.fixed_ip_address, self.dest_ip_address, self.dest_ip_address, self.fixed_ip_address)
        local_listen_dict['snat_host'] = "remote"

        tunnel_ip = discovery.get_tunnel_ip(self.source_host_id, self.neutron)
        local_listen_dict['tunnel_ip'] = tunnel_ip
        local_listen_dict['vxlan_filter'] = "(src %s or dst %s) and udp port (4789)" % (local_listen_dict['tunnel_ip'], local_listen_dict['tunnel_ip'])
        if local_listen_dict['network_type'] == "vxlan":
            local_listen_dict['tunnel_port'] = discovery.get_tunnel_port(self.source_host_id, local_listen_dict['tunnel_ip'], self.neutron)
        else:
            local_listen_dict['tunnel_port'] = "None"

        local_listen_dict['bridge_name'] = discovery.get_bridge_name(local_listen_dict['network_label'], self.source_host_id, self.neutron)
        local_listen_dict['tag'] = "VM SOURCE"
        local_listen_dict['vif_names'] = self.vif_names
        local_listen_dict['ns_vif_names'] = []
        vif_buffer = self.ns_vif_names
        for vif in vif_buffer:
            for vif_name in list(vif.keys()):
                if "qr" in vif_name:
                    local_listen_dict['ns_vif_names'].append(vif)
                    break


        remote_listen_dict = dict()
        remote_listen_dict['checker_type'] = "SNAT"
        remote_listen_dict['packet_type'] = "ICMP"
        remote_listen_dict['vm_name'] = self.vm_name
        remote_listen_dict['src_ip_address'] = self.fixed_ip_address
        remote_listen_dict['src_mac_address'] = self.source_port_dict['mac_address']
        remote_listen_dict['dest_ip_address'] = self.dest_ip_address
        remote_listen_dict['dest_mac_address'] = self.dest_mac_address
        remote_listen_dict['host_id'] = self.snat_host_id
        remote_listen_dict['port_id'] = self.source_port_dict['id']
        remote_listen_dict['network_label_remote_ext'] = discovery.get_network_label(self.external_network_id, self.neutron)
        remote_listen_dict['network_type_remote_ext'] = discovery.get_network_type(self.external_network_id, self.neutron)
        remote_listen_dict['network_label'] = discovery.get_network_label(self.tenant_network_id, self.neutron)
        remote_listen_dict['network_type'] = discovery.get_network_type(self.tenant_network_id, self.neutron)
        remote_listen_dict['nic_filter'] = "icmp and  ((src %s and dst %s) or (src %s and dst %s)) " % (self.fixed_ip_address, self.dest_ip_address, self.dest_ip_address, self.fixed_ip_address)
        remote_listen_dict['ext_nic_filter'] = "icmp and  ((src %s and dst %s) or (src %s and dst %s)) " % (self.snat_external_ip, self.dest_ip_address, self.dest_ip_address, self.snat_external_ip)

        tunnel_ip = discovery.get_tunnel_ip(self.snat_host_id, self.neutron)
        remote_listen_dict['tunnel_ip'] = tunnel_ip
        remote_listen_dict['vxlan_filter'] = "(src %s or dst %s) and udp port (4789)" % (remote_listen_dict['tunnel_ip'], remote_listen_dict['tunnel_ip'])
        if remote_listen_dict['network_type'] == "vxlan":
            remote_listen_dict['tunnel_port'] = discovery.get_tunnel_port(self.snat_host_id, remote_listen_dict['tunnel_ip'], self.neutron)
        else:
            remote_listen_dict['tunnel_port'] = "None"

        remote_listen_dict['bridge_name'] = discovery.get_bridge_name(remote_listen_dict['network_label'], self.snat_host_id, self.neutron)
        remote_listen_dict['bridge_name_remote_ext'] = discovery.get_bridge_name(remote_listen_dict['network_label_remote_ext'], self.snat_host_id, self.neutron)
        remote_listen_dict['tag'] = "SNAT NS"
        remote_listen_dict['vif_names'] = []
        remote_listen_dict['ns_vif_names'] = []
        for vif in vif_buffer:
            for vif_name in list(vif.keys()):
                if "qg" in vif_name or "sg" in vif_name:
                    remote_listen_dict['ns_vif_names'].append(vif)
                    break

        return local_listen_dict, remote_listen_dict

    def format_inject_dict(self):
        inject_icmp_dict = dict()
        inject_icmp_dict.update(self.local_listen_dict)
        inject_icmp_dict['payload'] = "abcd" * 3

        for vif in inject_icmp_dict['vif_names']:
            if "qbr" in list(vif.keys())[0]:
               inject_port = list(vif.keys())[0]
               break

        inject_icmp_dict['inject_port'] = inject_port

        return inject_icmp_dict

    def get_vif_list(self):

        vif_list = []
        vif_names = discovery.get_vif_names(self.source_port_dict['id'])
        for port_type, vif_name in vif_names.items():
            vif = dict()
            vif[vif_name] = dict()
            vif[vif_name]['filter'] = "icmp and ((src %s and dst %s) or (src %s and dst %s)) " % (self.fixed_ip_address, self.dest_ip_address, self.dest_ip_address, self.fixed_ip_address)
            vif[vif_name]['is_ns'] = "None"
            vif[vif_name]['port_type'] = port_type
            vif_list.append(vif)

        return vif_list

    def get_ns_vif_list(self):

        ns_vif_list = []
        ns_vif_names = discovery.get_snat_interfaces(self.router_id, self.qr_port_id, self.sg_port['id'], self.qg_port['id'])
        for vif_name, netns in ns_vif_names.items():
            vif = dict()
            vif[vif_name] = dict()
            if "qg" in vif_name:
            	vif[vif_name]['filter'] = "icmp and host %s and host %s " % (self.snat_external_ip, self.dest_ip_address)
            else:
                vif[vif_name]['filter'] = "icmp and host %s and host %s " % (self.fixed_ip_address, self.dest_ip_address)
            vif[vif_name]['is_ns'] = netns
            vif[vif_name]['port_type'] = vif_name
            ns_vif_list.append(vif)

        return ns_vif_list

    def determine_snat_host(self):

        if self.snat_host_id == self.source_host_id:
            self.flag = "local"
            return "local snat"
        else:
            self.flag = "remote"
            return "remote snat"

    def get_local_dict(self):
        return self.local_listen_dict

    def get_remote_dict(self):
        return self.remote_listen_dict

    def get_inject_dict(self):
        return self.inject_icmp_dict

    def get_flag(self):
        return self.flag
