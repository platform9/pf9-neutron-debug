import sys
sys.path.append("../")

import arp_dynamic_info
import dhcp_dynamic_info
import icmp_dynamic_info
import init_neutron_client
import logging
import pdb
import time

neutron = init_neutron_client.make_neutron_object()

def run_arp_checker(source_vm, client_obj):

    source_arp_dict, inject_arp_dict, host_dict = get_arp_info(source_vm)

    if source_arp_dict['network_type'] == "vxlan":
        client_obj.listen_on_host(source_arp_dict)
        time.sleep(3)
        client_obj.source_arp_inject(inject_arp_dict)
        time.sleep(3)
        arp_response_dict = client_obj.retrieve_listener_data(source_arp_dict)
        message, code = analyze_arp_data(host_dict, arp_response_dict)
    else:
        arp_response_dict = {}
        code = 0
        message = ""
    return arp_response_dict, message, code

def run_dhcp_checker(vm_name, client_obj):

    local, remote = dhcp_dynamic_info.create_dhcp_dict(vm_name, neutron)
    message = client_obj.check_dnsmasq_process(local['vm info'], local['vm info']['host_id'])
    print message
    logging.info(message)
    if "CODE 1" in message or "CODE 2" in message:
        sys.exit()
    for host in remote['dhcp remote hosts']:
        message = client_obj.check_dnsmasq_process(local['vm info'], host['host_id'])
        print message
	logging.info(message)
        if "CODE 1" in message or "CODE 2" in message:
            sys.exit()

    dhcp_response_list = []
    client_obj.send_dhcp_to_remote_hosts(remote)
    time.sleep(2)
    local_dhcp_response_dict = client_obj.local_host_recieve_dhcp_message(local)
    remote_dhcp_response_list = client_obj.retrieve_remote_dhcp_data(remote)

    return local_dhcp_response_dict, remote_dhcp_response_list

def run_icmp_checker(source_vm, dest_vm, client_obj):

    source_icmp_dict, dest_icmp_dict, inject_icmp_dict = get_icmp_info(source_vm, dest_vm)

    client_obj.listen_on_host(source_icmp_dict)
    client_obj.listen_on_host(dest_icmp_dict)
    time.sleep(3)
    client_obj.source_icmp_inject(inject_icmp_dict)
    time.sleep(3)
    source_response_dict = client_obj.retrieve_listener_data(source_icmp_dict)
    dest_response_dict = client_obj.retrieve_listener_data(dest_icmp_dict)

    return source_response_dict, dest_response_dict

def get_arp_info(vm_name):

    arp_info = arp_dynamic_info.ARPInfo(vm_name, neutron)
    source_arp_dict = arp_info.get_source_arp_dict()
    inject_arp_dict = arp_info.get_inject_arp_dict()
    host_dict = arp_info.get_vxlan_host_dict()
    return source_arp_dict, inject_arp_dict, host_dict

def analyze_arp_data(host_dict, arp_response_dict):

    expected_tunnel_ips = host_dict.values()
    actual_tunnel_ips = []
    for packet in arp_response_dict[arp_response_dict.keys()[0]]:
        actual_tunnel_ips.append(packet[3])

    diff = list(set(expected_tunnel_ips)-set(actual_tunnel_ips))

    if len(diff) == 0:
        message = "ARP Packet sent to every host with port on VXLAN Network"
        logging.info(message)
        code = 0
    else:
        message = "ARP Packet not sending to following host tunnel ips: %s" % diff
        logging.info(message)
        code = 1
    return message, code



def get_icmp_info(source_vm, dest_vm):

    icmp_info = icmp_dynamic_info.ICMPInfo(source_vm, dest_vm, neutron)
    source_icmp_dict = icmp_info.get_source_icmp_dict()
    dest_icmp_dict = icmp_info.get_dest_icmp_dict()
    inject_icmp_dict = icmp_info.get_inject_icmp_dict()
    return source_icmp_dict, dest_icmp_dict, inject_icmp_dict
