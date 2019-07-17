import sys
sys.path.append('../../common/')

import pdb
import os
import init_neutron_client
import discovery

DHCP_OWNER = 'network:dhcp'

def create_dhcp_dict(vm_name, neutron):

    vm_name = discovery.vmname_parse(vm_name)
    vm_port_dict = discovery.get_port_dict(vm_name, neutron)
    network_id = vm_port_dict['network_id']
    host_id = vm_port_dict['binding:host_id']
    dhcp_ports = discovery.get_all_dhcp_ports(network_id, neutron)
    
    network_label = discovery.get_network_label(network_id, neutron)
    dhcp_same_host, dhcp_different_host = differentiate_hosts(host_id, dhcp_ports)
    local_dhcp_dict, remote_dhcp_dict = format_dhcp_dict(vm_port_dict, dhcp_same_host, dhcp_different_host, network_label, neutron)

    return local_dhcp_dict, remote_dhcp_dict

def differentiate_hosts(vm_host_id, dhcp_ports):

    same_host = []
    different_host = []

    for dhcp_port in dhcp_ports:
        if dhcp_port['binding:host_id'] == vm_host_id:
            same_host.append(dhcp_port)
        else:
            different_host.append(dhcp_port)

    return same_host, different_host

def format_dhcp_dict(vm_port_dict, same_host, different_host, network_label, neutron):

    bridge_name = discovery.get_bridge_name(network_label, vm_port_dict['binding:host_id'], neutron)

    local_dhcp_dict = {}
    vm_info = {}
    vm_info['network_id'] = vm_port_dict['network_id']
    vm_info['port_id'] = vm_port_dict['id']
    vm_info['device_id'] = vm_port_dict['device_id']
    vm_info['host_id'] = vm_port_dict['binding:host_id']
    vm_info['network_label'] = network_label
    vm_info['mac_address'] = vm_port_dict['mac_address']
    vm_info['bridge_name'] = bridge_name
    local_dhcp_dict['vm info'] = vm_info

    dhcp_same_host = []
    for port in same_host:
        dhcp_same_host.append({'port_id':port['id']})
    local_dhcp_dict['dhcp local host'] = dhcp_same_host

    remote_dhcp_dict = {}
    dhcp_different_host = []
    for port in different_host:
        dhcp_host_id = port['binding:host_id']
	#print "dhcp port"
	#print port
        dhcp_bridge_name = discovery.get_bridge_name(network_label, dhcp_host_id, neutron)
        dhcp_different_host.append({'port_id':port['id'], 'network_label':network_label, 'network_id':port['network_id'], 'bridge_name':dhcp_bridge_name,
		'host_id':dhcp_host_id, 'src_mac_address':vm_port_dict['mac_address'], 'dhcp remote host':""})
    remote_dhcp_dict['dhcp remote hosts'] = dhcp_different_host

    return local_dhcp_dict, remote_dhcp_dict


# Main Function to test
if __name__ == "__main__":

    vm_name = sys.argv[1]
    neutron = init_neutron_client.make_neutron_object()

    # DHCP Dict
    d = create_dhcp_dict(vm_name, neutron)
    print d
