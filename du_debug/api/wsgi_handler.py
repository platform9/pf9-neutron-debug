import sys
sys.path.append("../")

from flask import Flask, request, Response, jsonify, make_response
from oslo_config import cfg
from oslo_log import log as logging
import importlib
import init_checker
import dhcp_static_info
import du_rpc_handler
import logging as logs
import oslo_messaging
import time
import pdb

CONF = cfg.CONF
CONF(sys.argv[1:])

app = Flask(__name__)
oslo_messaging.set_transport_defaults('myexchange')
logs.basicConfig(filename='/var/log/neutron_debug/neutron_debug.log', filemode = 'w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

@app.route('/neutron_debug/v1/dhcp/<string:vm_name>', methods=['GET'])
def dhcp_checker(vm_name):

    # Heartbeat static checks
    error_code = dhcp_static_info.run_du_static_checks(vm_name, init_checker.neutron)
    if error_code:
        return Response("Heartbeat Error detected -> VM Port, DHCP Port, or Host is down. Check /var/log/neutron_debug/neutron_debug.log for specific error\n", status=200)
    print("HEARTBEAT tests look OK, ready to move on")

    # Runs ARP checker if VXLAN
    client_obj = du_rpc_handler.RPCClientObject(CONF)
    arp_response_dict, message, code = init_checker.run_arp_checker(vm_name, client_obj)
    if code:
        return Response(message, status=200)

    # Runs DHCP checker and returns results from DHCP packet injection
    vm_response_dict, dhcp_response_list, dhcp_ns_response_list = init_checker.run_dhcp_checker(vm_name, client_obj)

    for data_dict in dhcp_response_list:
        vm_response_dict.update(data_dict)
    for data_dict in dhcp_ns_response_list:
        vm_response_dict.update(data_dict)

    message = basic_analysis(vm_response_dict)
    resp = make_response(message, 200)
    return resp


@app.route('/neutron_debug/v1/fip/<string:vm_name>', methods=['GET'])
def fip_checker(vm_name):
    """
    Init RPC Client, runs FIP checker and return results
    """

    client_obj = du_rpc_handler.RPCClientObject(CONF)
    fip_response_dict = init_checker.run_fip_checker(vm_name, client_obj)

    message = basic_analysis(fip_response_dict)
    resp = make_response(message, 200)
    return resp

@app.route('/neutron_debug/v1/snat/<string:vm_name>', methods=['GET'])
def snat_checker(vm_name):
    """
    Init RPC Client, runs SNAT checker and return results
    """

    client_obj = du_rpc_handler.RPCClientObject(CONF)
    snat_response_dict = init_checker.run_snat_checker(vm_name, client_obj)

    message = basic_analysis(snat_response_dict)
    resp = make_response(message, 200)
    return resp

@app.route('/neutron_debug/v1/ping/<string:source_vm>/<string:dest_vm>', methods=['GET'])
def ping_vms_checker(source_vm, dest_vm):
    """
    Init RPC Client, runs ping checker and return results
    """

    client_obj = du_rpc_handler.RPCClientObject(CONF)
    arp_response_dict, message, code = init_checker.run_arp_checker(source_vm, client_obj)
    if code:
        return Response(message, status=200)

    source_icmp_response_dict, dest_icmp_response_dict = init_checker.run_icmp_checker(source_vm, dest_vm, client_obj)

    ping_dict = dict()
    ping_dict.update(arp_response_dict)
    ping_dict.update(source_icmp_response_dict)
    ping_dict.update(dest_icmp_response_dict)

    message = basic_analysis(ping_dict)
    resp = make_response(message, 200)
    return resp

def basic_analysis(response):
    """
    Basic Anlysis to determine if packets are missing
    """

    packet_flag = True
    for vif, data in response.items():
        if len(data) == 0:
            packet_flag = False

    if packet_flag:
        message = "Packets detected at every plumbing point, but check /var/log/neutron_debug/neutron_debug.log for more details.\n"
    else:
        message = "Packets missing at one or more plumbing points, check /var/log/neutron_debug/neutron_debug.log for more details.\n"
    return message

def app_factory(global_config, **local_conf):
    return app
