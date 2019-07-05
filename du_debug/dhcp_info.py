from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client
import pdb
import os
import sys
from keystoneauth1 import identity
from keystoneauth1 import session
import init_neutron_client

DHCP_OWNER = 'network:dhcp'

def create_dhcp_dict(vm_name, neutron):

    vm_name = vmname_parse(vm_name)
    vm_port_dict = get_port_dict(vm_name, neutron)
    network_id = vm_port_dict['network_id']
    host_id = vm_port_dict['binding:host_id']

    dhcp_ports = get_all_dhcp_ports(network_id, neutron)
    network_label = get_network_label(network_id, neutron)
    dhcp_same_host, dhcp_different_host = differentiate_hosts(host_id, dhcp_ports)
    dhcp_dict = format_dhcp_dict(vm_port_dict, dhcp_same_host, dhcp_different_host, network_label)

    return dhcp_dict

def vmname_parse(vm_name):
    vm_name = vm_name.replace("_", "-")
    return vm_name    

def get_port_dict(vm_name, neutron):
    for port in neutron.list_ports()['ports']:
	if port['dns_name'] == vm_name:
            return port

def get_all_dhcp_ports(vm_network_id, neutron):
    dhcp_ports = []

    for port in neutron.list_ports()['ports']:
        if port['network_id'] == vm_network_id and port['device_owner'] == DHCP_OWNER:
            dhcp_ports.append(port)

    return dhcp_ports

def differentiate_hosts(vm_host_id, dhcp_ports):

    same_host = []
    different_host = []

    for dhcp_port in dhcp_ports:
        if dhcp_port['binding:host_id'] == vm_host_id:
            same_host.append(dhcp_port)
        else:
            different_host.append(dhcp_port)

    return same_host, different_host

def get_network_label(vm_network_id, neutron):
    for network in neutron.list_networks()['networks']:
	if network['id'] == vm_network_id:
	    return network['provider:physical_network'] 

def format_dhcp_dict(vm_port_dict, same_host, different_host, network_label):

    dhcp_dict = {}

    vm_info = {}
    vm_info['network_id'] = vm_port_dict['network_id']
    vm_info['port_id'] = vm_port_dict['id']
    vm_info['device_id'] = vm_port_dict['device_id']
    vm_info['host_id'] = vm_port_dict['binding:host_id']
    vm_info['network_label'] = network_label
    dhcp_dict['vm info'] = vm_info

    dhcp_same_host = []
    for port in same_host:
        dhcp_same_host.append({'port_id':port['id']})
    dhcp_dict['dhcp local host'] = dhcp_same_host

    dhcp_different_host = []
    for port in different_host:
        dhcp_different_host.append({'port_id':port['id'], 'network_label':network_label})
    dhcp_dict['dhcp remote host'] = dhcp_different_host

    return dhcp_dict


# Main Function to test
if __name__ == "__main__":

    vm_name = sys.argv[1]
    neutron = init_neutron_client.make_neutron_object()

    # DHCP Dict
    d = create_dhcp_dict(vm_name, neutron)
    print d
