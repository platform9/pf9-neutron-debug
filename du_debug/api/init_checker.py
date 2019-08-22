import sys
sys.path.append("../")

import arp_dynamic_info
import dhcp_dynamic_info
import icmp_dynamic_info
import init_neutron_client
import fip_dynamic_info
import snat_dynamic_info
import logging
import pdb
import time
import coloredlogs

neutron = init_neutron_client.make_neutron_object()

#logging.basicConfig(filename='/var/log/neutron_debug/neutron_debug.log', filemode = 'w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
logger = logging.getLogger("main_logger")

fh = logging.FileHandler('/var/log/neutron_debug/neutron_debug.log')
fh.setLevel(logging.DEBUG)

formatter = coloredlogs.ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

coloredlogs.install(level='DEBUG')


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

    vm_dict, dhcp_list, inject_dict = get_dhcp_info(vm_name)
    print("VM DICT")
    print(vm_dict)
    print("DHCP LIST")
    print(dhcp_list)
    print("INJECT DICT")
    print(inject_dict)

    for dhcp_dict in dhcp_list:
        message = client_obj.check_dnsmasq_process(vm_dict, dhcp_dict['host_id'])
        logger.info(message)
        if "CODE 1" in message or "CODE 2" in message:
           sys.exit()
    logger.info("")

    client_obj.listen_on_host(vm_dict)
    for dhcp_dict in dhcp_list:
        if dhcp_dict['host_id'] != vm_dict['host_id']:
           client_obj.listen_on_host(dhcp_dict)
        client_obj.listen_ns_on_host(dhcp_dict)
    time.sleep(3)
    client_obj.source_dhcp_inject(inject_dict)
    time.sleep(3)
    vm_response_dict = client_obj.retrieve_listener_data(vm_dict)
    dhcp_response_list = []
    dhcp_ns_response_list = []
    for dhcp_dict in dhcp_list:
        if dhcp_dict['host_id'] != vm_dict['host_id']:
           dhcp_response_list.append(client_obj.retrieve_listener_data(dhcp_dict))
        dhcp_ns_response_list.append(client_obj.retrieve_ns_listener_data(dhcp_dict))

    return vm_response_dict, dhcp_response_list, dhcp_ns_response_list

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

def run_fip_checker(vm_name, client_obj):

    listen_fip_dict, inject_fip_dict = get_fip_info(vm_name)

    client_obj.listen_on_host(listen_fip_dict)
    client_obj.listen_ns_on_host(listen_fip_dict)
    time.sleep(3)
    client_obj.source_icmp_inject(inject_fip_dict)
    time.sleep(3)
    fip_response_dict = client_obj.retrieve_listener_data(listen_fip_dict)
    fip_ns_response_dict = client_obj.retrieve_ns_listener_data(listen_fip_dict)

    fip_response_dict.update(fip_ns_response_dict)

    return fip_response_dict

def run_snat_checker(vm_name, client_obj):

    listen_local_snat_dict, listen_remote_snat_dict, inject_snat_dict, flag = get_snat_info(vm_name)

    print("LOCAL SNAT")
    print(listen_local_snat_dict)
    print("REMOTE SNAT")
    print(listen_remote_snat_dict)

    snat_resp = dict()

    if flag == "local":
        client_obj.listen_on_host(listen_local_snat_dict)
        client_obj.listen_ns_on_host(listen_local_snat_dict)
        time.sleep(3)
        client_obj.source_icmp_inject(inject_snat_dict)
        time.sleep(3)
        snat_local_response_dict = client_obj.retrieve_listener_data(listen_local_snat_dict)
        snat_local_ns_response_dict = client_obj.retrieve_ns_listener_data(listen_local_snat_dict)

        snat_resp.update(snat_local_response_dict)
        snat_resp.update(snat_local_ns_response_dict)
    elif flag == "remote":
        client_obj.listen_on_host(listen_local_snat_dict)
        client_obj.listen_ns_on_host(listen_local_snat_dict)
        client_obj.listen_on_host(listen_remote_snat_dict)
        client_obj.listen_ns_on_host(listen_remote_snat_dict)
        time.sleep(2)
        client_obj.source_icmp_inject(inject_snat_dict)
        time.sleep(1)
        snat_local_response_dict = client_obj.retrieve_listener_data(listen_local_snat_dict)
        snat_local_ns_response_dict = client_obj.retrieve_ns_listener_data(listen_local_snat_dict)
        snat_remote_response_dict = client_obj.retrieve_listener_data(listen_remote_snat_dict)
        snat_remote_ns_response_dict = client_obj.retrieve_ns_listener_data(listen_remote_snat_dict)
        snat_resp.update(snat_local_response_dict)
        snat_resp.update(snat_local_ns_response_dict)
        snat_resp.update(snat_remote_response_dict)
        snat_resp.update(snat_remote_ns_response_dict)

    return snat_resp


def get_arp_info(vm_name):

    arp_info = arp_dynamic_info.ARPInfo(vm_name, neutron)
    source_arp_dict = arp_info.get_source_arp_dict()
    inject_arp_dict = arp_info.get_inject_arp_dict()
    host_dict = arp_info.get_vxlan_host_dict()
    return source_arp_dict, inject_arp_dict, host_dict

def analyze_arp_data(host_dict, arp_response_dict):

    expected_tunnel_ips = host_dict.values()
    actual_tunnel_ips = []
    for packet in arp_response_dict[list(arp_response_dict.keys())[0]]:
        actual_tunnel_ips.append(packet[3])

    diff = list(set(expected_tunnel_ips)-set(actual_tunnel_ips))

    if len(diff) == 0:
        message = "ARP Packet sent to every host with port on VXLAN Network"
        logger.info(message)
        code = 0
    else:
        message = "ARP Packet not sending to following host tunnel ips: %s" % diff
        logger.info(message)
        code = 1

    logger.info("")
    return message, code

def get_dhcp_info(vm_name):
    dhcp_info = dhcp_dynamic_info.DHCPInfo(vm_name, neutron)
    vm_dict = dhcp_info.get_vm_dict()
    dhcp_list = dhcp_info.get_dhcp_list()
    inject_dict = dhcp_info.get_inject_dict()
    return vm_dict, dhcp_list, inject_dict

def get_icmp_info(source_vm, dest_vm):

    icmp_info = icmp_dynamic_info.ICMPInfo(source_vm, dest_vm, neutron)
    source_icmp_dict = icmp_info.get_source_icmp_dict()
    dest_icmp_dict = icmp_info.get_dest_icmp_dict()
    inject_icmp_dict = icmp_info.get_inject_icmp_dict()
    return source_icmp_dict, dest_icmp_dict, inject_icmp_dict

def get_fip_info(vm_name):

    fip_info = fip_dynamic_info.FIPInfo(vm_name, neutron)
    listen_fip_dict = fip_info.get_listen_fip_dict()
    inject_fip_dict = fip_info.get_inject_fip_dict()
    return listen_fip_dict, inject_fip_dict

def get_snat_info(vm_name):

    snat_info = snat_dynamic_info.SNATInfo(vm_name, neutron)
    listen_local_snat_dict = snat_info.get_local_dict()
    listen_remote_snat_dict = snat_info.get_remote_dict()
    inject_snat_dict = snat_info.get_inject_dict()
    flag = snat_info.get_flag()

    return listen_local_snat_dict, listen_remote_snat_dict, inject_snat_dict, flag
