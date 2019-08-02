import sys
sys.path.append("../")

from flask import Flask, request, Response, jsonify, make_response
from oslo_config import cfg
from oslo_log import log as logging
import importlib
import init_checker
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

    client_obj = du_rpc_handler.RPCClientObject(CONF)
    arp_response_dict = init_checker.run_arp_checker(vm_name, client_obj)
    local_dhcp_response_dict, remote_dhcp_response_list = init_checker.run_dhcp_checker(vm_name, client_obj)

    response_list = remote_dhcp_response_list
    response_list.append(local_dhcp_response_dict)
    response_list.append(arp_response_dict)

    resp = make_response(jsonify(response_list), 200)
    resp.headers['Packet Data'] = 'THERE'
    return resp

@app.route('/v1/pair/<string:source_vm>/<string:dest_vm>', methods=['GET'])
def paired_vms_checker(source_vm, dest_vm):

    client_obj = du_rpc_handler.RPCClientObject(CONF)
    arp_response_dict = init_checker.run_arp_checker(source_vm, client_obj)
    source_icmp_response_dict, dest_icmp_response_dict = init_checker.run_icmp_checker(source_vm, dest_vm, client_obj)

    response_list = [arp_response_dict, source_icmp_response_dict, dest_icmp_response_dict]

    resp = make_response(jsonify(response_list), 200)
    resp.headers['Packet Data'] = 'THERE'
    return resp


def app_factory(global_config, **local_conf):
    return app
