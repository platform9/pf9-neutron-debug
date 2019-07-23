import sys
sys.path.append("../")

from flask import Flask, request, Response, jsonify
from oslo_config import cfg
from oslo_log import log as logging
import importlib
import init_neutron_client
import dhcp_dynamic_info
import dhcp_static_info
import du_debug
import icmp_dynamic_info
import log_data
import time

CONF = cfg.CONF
app = Flask(__name__)

neutron = init_neutron_client.make_neutron_object()


#@app.route('/v1/single/<string:vm_name>', methods=['GET'])
#def single_vm_checker(vm_name):

@app.route('/v1/pair/<string:source_vm>/<string:dest_vm>', methods=['GET'])
def paired_vms_checker(source_vm, dest_vm):

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

    if request.method == 'GET':
        du_debug.listen_on_host(source_icmp_dict)
        du_debug.listen_on_host(dest_icmp_dict)
        time.sleep(3)
        du_debug.source_inject(inject_icmp_dict)
        time.sleep(3)
        du_debug.retrieve_listener_data(source_icmp_dict)
        du_debug.retrieve_listener_data(dest_icmp_dict)


def app_factory(global_config, **local_conf):
    return app
