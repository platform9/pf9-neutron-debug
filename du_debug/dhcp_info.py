from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client
import pdb
import os
from keystoneauth1 import identity
from keystoneauth1 import session

DHCP_OWNER = 'network:dhcp'

def create_dhcp_dict(vm_name, neutron):

    dhcp_dict = {}

    vm_port_dict = get_port_dict(vm_name, neutron)

    network_id = vm_port_dict['network_id']
    port_id = vm_port_dict['id']
    device_id = vm_port_dict['device_id']
    host_id = vm_port_dict['binding:host_id']

    dhcp_ports = get_all_dhcp_ports(network_id, neutron)




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
        if dhcp_port['binding:host_id'] == vm_host_id"
