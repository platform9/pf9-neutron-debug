import os
import sys
import requests

def vmname_parse(vm_name):
    vm_name = vm_name.replace("_", "-")
    return vm_name

def get_port_dict(vm_name, neutron):
    for port in neutron.list_ports()['ports']:
        if port['dns_name'] == vm_name:
            return port

def get_network_label(vm_network_id, neutron):
    for network in neutron.list_networks()['networks']:
        if network['id'] == vm_network_id:
            return network['provider:physical_network']

def get_bridge_name(network_label, host_id, neutron):
    auth_token = neutron.get_auth_info()['auth_token']
    r = requests.get('https://neutrondebug.platform9.horse/resmgr/v1/hosts/%s/roles/pf9-neutron-ovs-agent' % (host_id),
                    headers={'x-auth-token': auth_token, 'Content-type': 'application/json'})
    mappings_dict = r.json()['bridge_mappings']
    mappings = mappings_dict.split(',')
    for mapping in mappings:
        parts = mapping.split(':')
        if parts[0] == network_label:
            return parts[1]
