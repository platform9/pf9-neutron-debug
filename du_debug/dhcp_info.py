from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client
import pdb
import os
from keystoneauth1 import identity
from keystoneauth1 import session
import init_neutron_client

DHCP_OWNER = 'network:dhcp'

def create_dhcp_dict(vm_name, neutron):

    vm_port_dict = get_port_dict(vm_name, neutron)
    network_id = vm_port_dict['network_id']
    host_id = vm_port_dict['binding:host_id']

    dhcp_ports = get_all_dhcp_ports(network_id, neutron)
    dhcp_same_host, dhcp_different_host = differentiate_hosts(host_id, dhcp_ports)
    dhcp_dict = format_dhcp_dict(vm_port_dict, dhcp_same_host, dhcp_different_host)

    return dhcp_dict

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

def format_dhcp_dict(vm_port_dict, same_host, different_host):

    dhcp_dict = {}

    vm_info = {}
    vm_info['network_id'] = vm_port_dict['network_id']
    vm_info['port id'] = vm_port_dict['id']
    vm_info['device_id'] = vm_port_dict['device_id']
    vm_info['host_id'] = vm_port_dict['binding:host_id']
    ## TODO: Figure out vm physical port
    #vm_info['nic'] =
    dhcp_dict['vm info'] = vm_info

    dhcp_same_host = []
    for port in same_host:
        dhcp_same_host.append(port['device_id'])
    dhcp_dict['dhcp same host'] = dhcp_same_host

    # TODO: Figure out dhcp physial port
    #dhcp_different_host = []
    #for port in same_host:
    #    dhcp_different_host.append({'device_id':port['device_id'], 'nic':port['nic']})
    #dhcp_dict['dhcp different host'] = dhcp_different_host

    return dhcp_dict


# Main Function to test
if __name__ == "__main__":

    vm_name = sys.arg[1]
    neutron = init_neutron_client.make_neutron_object()

    # DHCP Dict
    dict = create_dhcp_dict(vm_name, neutron)
    print dict
