# DU Server for RPC messaging

import sys
sys.path.append('../common/')
sys.path.append('./dhcp/')

import time
import oslo_messaging
import eventlet
import init_neutron_client
import dhcp_dynamic_info
import dhcp_static_info
import log_data
import threading
import logging as logs

from oslo_config import cfg
from oslo_log import log as logging
from multiprocessing import Pool

CONF = cfg.CONF

logging.register_options(CONF)
logging.set_defaults()
LOG = logging.getLogger(__name__)


stop_thread = False

# Return Endpoint
class GetHostDataEndpoint(object):
    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server
        self.counter = 0

    def get_dict(self, ctx, d):
        print "_______________RETURNED JSON___________________"
        print d
        global stop_thread
        log_data.log_data(d)
        self.counter = self.counter + 1
        if self.counter == 2:
            stop_thread = True

    def get_message(self, ctx, message):
        logs.info(message)
        print message
        if "CODE 0" in message or "CODE 1" in message:
            stop_thread = True


def main():
    opts = [cfg.StrOpt('host')]
    CONF.register_opts(opts)

    stop_thread = False
    CONF(sys.argv[2:])

    vm_name = sys.argv[1]

    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server='myserver', version='2.0', namespace='test')
    server = create_server(CONF, transport, target)
    client = oslo_messaging.RPCClient(transport, target)

    neutron = init_neutron_client.make_neutron_object()

    error_code = dhcp_static_info.run_du_static_checks(vm_name, neutron)

    if error_code:
        sys.exit("Static Error detected -> VM Port, DHCP Port, or Host is down. Check /var/log/neutron_debug/static.log for specific error")

    print "HEARTBEAT tests look OK, ready to move on"

    server_thread = threading.Thread(target=server_process, args=(server,))
    server_thread.start()

    # DHCP Dict
    local, remote = dhcp_dynamic_info.create_dhcp_dict(vm_name, neutron)

    #dnsmasq
    check_dnsmasq_process(client, local['vm info'], local['vm info']['host_id'])

    for host in remote['dhcp remote hosts']:
        check_dnsmasq_process(client, local['vm info'], host['host_id'])

    #print local
    #print remote
    send_to_remote_hosts(client, remote)
    time.sleep(2)
    local_host_recieve_message(client, local)
    time.sleep(5)
    get_remote_data(client, remote)
    server_thread.join()


def server_process(rpcserver):
    try:
        rpcserver.start()
	print "Server Starting..."
        for i in range(0,35):
           time.sleep(1)
           if stop_thread:
	      print("All done..Stopping Server")
              rpcserver.stop()
	      break
    except KeyboardInterrupt:
        print("Stopping server")

def create_server(conf, transport, target):
    """
    Create RPC server for handling messaging
    """
    endpoints = [GetHostDataEndpoint(None)]
    server = oslo_messaging.get_rpc_server(transport, target, endpoints, executor='blocking')
    return server

# RPC Message Functions
def send_to_remote_hosts(client, remote):
    for host in remote['dhcp remote hosts']:
        remote_host_recieve_message(client, host)

def local_host_recieve_message(client, dhcp_dict):

    cctxt = client.prepare(server=dhcp_dict['vm info']['host_id'])
    cctxt.cast({}, 'get_dhcp_dict', dhcp_d = dhcp_dict)

def remote_host_recieve_message(client, dhcp_dict):

    cctxt = client.prepare(server=dhcp_dict['host_id'])
    cctxt.cast({}, 'get_dhcp_dict', dhcp_d = dhcp_dict)

def get_remote_data(client, remote):
    for host in remote['dhcp remote hosts']:
        cctxt = client.prepare(server=host['host_id'])
        cctxt.cast({}, 'get_remote_listener_data', remote=host)

def check_dnsmasq_process(client, dhcp_dict, host_id):

    cctxt = client.prepare(server=host_id)
    cctxt.cast({}, 'dnsmasq_check', dhcp_d = dhcp_dict, host_id = host_id)


if __name__ == '__main__':
    main()
