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

@app.route('/v1/single/<string:vm_name>', methods=['GET'])
def single_vm_checker(vm_name):

    error_code = dhcp_static_info.run_du_static_checks(vm_name, init_checker.neutron)
    if error_code:
        sys.exit("Static Error detected -> VM Port, DHCP Port, or Host is down. Check /var/log/neutron_debug/neutron_debug.log for specific error")
    print "HEARTBEAT tests look OK, ready to move on"

<<<<<<< HEAD
    client_obj = du_rpc_handler.RPCClientObject(CONF)
    arp_response_dict, message, code = init_checker.run_arp_checker(vm_name, client_obj)
    if code:
        return Response(message, status=200)

    local_dhcp_response_dict, remote_dhcp_response_list = init_checker.run_dhcp_checker(vm_name, client_obj)

    response_list = remote_dhcp_response_list
    response_list.append(local_dhcp_response_dict)
    response_list.append(arp_response_dict)

    resp = make_response(jsonify(response_list), 200)
    resp.headers['Packet Data'] = 'THERE'
    return resp

@app.route('/v1/single/fip/<string:vm_name>', methods=['GET'])
def fip_checker(vm_name):

    client_obj = du_rpc_handler.RPCClientObject(CONF)
    fip_response_dict = init_checker.run_fip_checker(vm_name, client_obj)

    resp = make_response(jsonify(fip_response_dict), 200)
=======
    client_obj = du_rpc_handler.RPCClientObject(CONF)
    arp_response_dict, message, code = init_checker.run_arp_checker(vm_name, client_obj)
    if code:
        return Response(message, status=200)

    local_dhcp_response_dict, remote_dhcp_response_list = init_checker.run_dhcp_checker(vm_name, client_obj)

    response_list = remote_dhcp_response_list
    response_list.append(local_dhcp_response_dict)
    response_list.append(arp_response_dict)

    resp = make_response(jsonify(response_list), 200)
    resp.headers['Packet Data'] = 'THERE'
>>>>>>> 0d26d143e58de51188334d43635a8cebbfa75cdd
    return resp

@app.route('/v1/pair/<string:source_vm>/<string:dest_vm>', methods=['GET'])
def paired_vms_checker(source_vm, dest_vm):

    client_obj = du_rpc_handler.RPCClientObject(CONF)
    arp_response_dict, message, code = init_checker.run_arp_checker(source_vm, client_obj)
    if code:
        return Response(message, status=200)

    source_icmp_response_dict, dest_icmp_response_dict = init_checker.run_icmp_checker(source_vm, dest_vm, client_obj)

    response_list = [arp_response_dict, source_icmp_response_dict, dest_icmp_response_dict]

    resp = make_response(jsonify(response_list), 200)
    resp.headers['Packet Data'] = 'THERE'
    return resp


def app_factory(global_config, **local_conf):
    return app
