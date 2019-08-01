import sys
sys.path.append("../")

from flask import Flask, request, Response, jsonify, make_response
from oslo_config import cfg
from oslo_log import log as logging
import importlib
import arp_dynamic_info
import init_neutron_client
import dhcp_dynamic_info
import dhcp_static_info
import du_rpc_handler
import icmp_dynamic_info
import log_data
import logging as logs
import oslo_messaging
import time
import pdb

CONF = cfg.CONF
CONF(sys.argv[1:])

app = Flask(__name__)
neutron = init_neutron_client.make_neutron_object()
oslo_messaging.set_transport_defaults('myexchange')

@app.route('/v1/single/<string:vm_name>', methods=['GET'])
def single_vm_checker(vm_name):

    ## TODO: global stop_thread

    error_code = dhcp_static_info.run_du_static_checks(vm_name, neutron)
    if error_code:
        #stop_thread = True
        sys.exit("Static Error detected -> VM Port, DHCP Port, or Host is down. Check /var/log/neutron_debug/neutron_debug.log for specific error")

    print "HEARTBEAT tests look OK, ready to move on"

    # DHCP Dict
    arp_info = arp_dynamic_info.ARPInfo(vm_name, neutron)
    source_arp_dict = arp_info.get_source_arp_dict()
    inject_arp_dict = arp_info.get_inject_arp_dict()


    local, remote = dhcp_dynamic_info.create_dhcp_dict(vm_name, neutron)

    client_obj = du_rpc_handler.RPCClientObject(CONF)

    message = client_obj.check_dnsmasq_process(local['vm info'], local['vm info']['host_id'])
    logs.info(message)
    print message
    if "CODE 1" in message or "CODE 2" in message:
        stop_thread = True
        sys.exit()
    for host in remote['dhcp remote hosts']:
        message = client_obj.check_dnsmasq_process(local['vm info'], host['host_id'])
        logs.info(message)
        print message
	if "CODE 1" in message or "CODE 2" in message:
            stop_thread = True
            sys.exit()

    dhcp_response_list = []
    if request.method == 'GET':

        if source_arp_dict['network_type'] == "vxlan":
            client_obj.listen_on_host(source_arp_dict)
            time.sleep(3)
            client_obj.source_arp_inject(inject_arp_dict)
            time.sleep(3)
            arp_response_dict = client_obj.retrieve_listener_data(source_arp_dict)

        client_obj.send_dhcp_to_remote_hosts(remote)
        time.sleep(2)
        local_dhcp_response_dict = client_obj.local_host_recieve_dhcp_message(local)
        #time.sleep(7)
        remote_dhcp_response_list = client_obj.retrieve_remote_dhcp_data(remote)

    dhcp_response_list = remote_dhcp_response_list
    dhcp_response_list.append(local_dhcp_response_dict)
    dhcp_response_list.append(arp_response_dict)

    resp = make_response(jsonify(dhcp_response_list), 200)
    resp.headers['Packet Data'] = 'THERE'
    return resp

@app.route('/v1/pair/<string:source_vm>/<string:dest_vm>', methods=['GET'])
def paired_vms_checker(source_vm, dest_vm):

    #pdb.set_trace()
    arp_info = arp_dynamic_info.ARPInfo(source_vm, neutron)
    source_arp_dict = arp_info.get_source_arp_dict()
    inject_arp_dict = arp_info.get_inject_arp_dict()

    icmp_info = icmp_dynamic_info.ICMPInfo(source_vm, dest_vm, neutron)
    source_icmp_dict = icmp_info.get_source_icmp_dict()
    dest_icmp_dict = icmp_info.get_dest_icmp_dict()
    inject_icmp_dict = icmp_info.get_inject_icmp_dict()

    print "SOURCE ICMP DICT"
    print source_icmp_dict
    print "DESTINATION ICMP DICT"
    print dest_icmp_dict
    print "INJECT SOURCE ICMP DICT"
    print inject_icmp_dict

    client_obj = du_rpc_handler.RPCClientObject(CONF)

    if request.method == 'GET':
        if source_arp_dict['network_type'] == "vxlan":
            client_obj.listen_on_host(source_arp_dict)
            time.sleep(3)
            client_obj.source_arp_inject(inject_arp_dict)
            time.sleep(3)
            arp_response_dict = client_obj.retrieve_listener_data(source_arp_dict)

        client_obj.listen_on_host(source_icmp_dict)
        client_obj.listen_on_host(dest_icmp_dict)
        time.sleep(3)
        client_obj.source_icmp_inject(inject_icmp_dict)
        time.sleep(3)
        source_response_dict = client_obj.retrieve_listener_data(source_icmp_dict)
        dest_response_dict = client_obj.retrieve_listener_data(dest_icmp_dict)

    response_list = [arp_response_dict, source_response_dict, dest_response_dict]
    
    resp = make_response(jsonify(response_list), 200)
    resp.headers['Packet Data'] = 'THERE'
    return resp

def app_factory(global_config, **local_conf):
    return app
