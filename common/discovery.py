import os
import sys
import requests

VIF_PREFIX_LEN = 14

# DU Side
def heartbeat_host(host_id, neutron):
    auth_token = neutron.get_auth_info()['auth_token']
    r = requests.get('https://neutrondebug.platform9.horse/resmgr/v1/hosts', headers={'x-auth-token': auth_token, 'Content-type': 'application/json'})
    for host in r.json():
        if host_id == host['id']:
            if host['info']['responding'] == True:
                return 1
            else:
                return 0

def heartbeat_port(port, neutron):
    if port['status'] == 'ACTIVE':
        return 1
    else
        return 0

def vmname_parse(vm_name):
    vm_name = vm_name.replace("_", "-")
    return vm_name

def get_all_dhcp_ports(vm_network_id, neutron):
    dhcp_ports = []

    for port in neutron.list_ports()['ports']:
        if port['network_id'] == vm_network_id and port['device_owner'] == DHCP_OWNER:
            dhcp_ports.append(port)

    return dhcp_ports

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


# HOST Side
def concat_vif_name(device_name, port_id):
    full_name = device_name + port_id
    return full_name[:VIF_PREFIX_LEN]

def get_vif_names(port_id):
    vif_names = {}
    tap_device = concat_vif_name("tap", port_id)
    qvb_device = concat_vif_name("qvb", port_id)
    qbr_device = concat_vif_name("qbr", port_id)
    qvo_device = concat_vif_name("qvo", port_id)

    vif_names = {"tap":tap_device, "qvb":qvb_device,
                 "qvo":qvo_device, "qbr":qbr_device}
    return vif_names
