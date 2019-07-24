# DU Server for RPC messaging

import sys
sys.path.append('../common/')
sys.path.append('./dhcp/')
sys.path.append('./icmp/')
sys.path.append('./api')

import time
import oslo_messaging
import eventlet
import init_neutron_client
import dhcp_dynamic_info
import dhcp_static_info
import icmp_dynamic_info
import log_data
import threading
import logging as logs
import pdb

from eventlet import wsgi
from oslo_config import cfg
from oslo_log import log as logging
from paste.deploy import loadapp

CONF = cfg.CONF

cli_opts = [
    cfg.StrOpt('paste_ini',default='/home/pranav/pf9-neutron-debug/du_debug/api/api-paste.ini')
]
paste_opts = [
    cfg.IntOpt('listen_port', default=8330)
]

CONF.register_cli_opts(cli_opts)
CONF.register_opts(paste_opts)

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
        self.log_info = log_data.LogData()

    def recieve_dict(self, ctx, d):
        print "_______________RETURNED JSON___________________"
        print d
        global stop_thread
        self.log_info.log_data(d)
        self.counter = self.counter + 1
        if self.counter == 2:
            # DHCP analysis
            #self.log_info.analyze()
            stop_thread = True

    def get_message(self, ctx, message):
        logs.info(message)
        print message
        if "CODE 0" in message or "CODE 1" in message:
            stop_thread = True


def main():

    stop_thread = False

    CONF(sys.argv[1:])

    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server='myserver', version='2.0', namespace='test')
    server = create_server(CONF, transport, target)

    server.start()
    server.stop()
    server.wait()

    server_thread = threading.Thread(target=server_process, args=(server,))
    server_thread.start()

    start_wsgi_server()

def start_wsgi_server():

    paste_file = CONF.paste_ini
    wsgi_app = loadapp('config:%s' % paste_file, "main")
    listen_port = CONF.listen_port
    wsgi.server(eventlet.listen(('', listen_port)), wsgi_app)

def run_dhcp_check(client, neutron):

    global stop_thread
    vm_name = sys.argv[1]

    error_code = dhcp_static_info.run_du_static_checks(vm_name, neutron)
    if error_code:
	stop_thread = True
        sys.exit("Static Error detected -> VM Port, DHCP Port, or Host is down. Check /var/log/neutron_debug/neutron_debug.log for specific error")

    print "HEARTBEAT tests look OK, ready to move on"

    # DHCP Dict
    local, remote = dhcp_dynamic_info.create_dhcp_dict(vm_name, neutron)
    #dnsmasq
    message = check_dnsmasq_process(client, local['vm info'], local['vm info']['host_id'])
    logs.info(message)
    print message
    if "CODE 1" in message or "CODE 2" in message:
        stop_thread = True
	sys.exit()
    for host in remote['dhcp remote hosts']:
        message = check_dnsmasq_process(client, local['vm info'], host['host_id'])
        logs.info(message)
        print message
	if "CODE 1" in message or "CODE 2" in message:
            stop_thread = True
	    sys.exit()

    send_dhcp_to_remote_hosts(client, remote)
    time.sleep(2)
    local_host_recieve_dhcp_message(client, local)
    time.sleep(7)
    retrieve_remote_dhcp_data(client, remote)


def server_process(rpcserver):
    try:
	rpcserver.reset()
        rpcserver.start()
	print "Server Starting..."
        #for i in range(0,35):
        while True:
           time.sleep(1)
           if stop_thread:
	      print("All done..Stopping Server")
              rpcserver.stop()
	      rpcserver.wait()
	      break
    except KeyboardInterrupt:
        rpcserver.stop()
	rpcserver.wait()
        print("Stopping server")

def create_server(conf, transport, target):
    """
    Create RPC server for handling messaging
    """
    endpoints = [GetHostDataEndpoint(None)]
    server = oslo_messaging.get_rpc_server(transport, target, endpoints, executor='blocking')
    return server

'''
# DHCP RPC Message Functions
def send_dhcp_to_remote_hosts(client, remote):
    for host in remote['dhcp remote hosts']:
        remote_host_recieve_dhcp_message(client, host)

def remote_host_recieve_dhcp_message(client, dhcp_dict):
    cctxt = client.prepare(server=dhcp_dict['host_id'])
    cctxt.cast({}, 'init_dhcp', dhcp_d = dhcp_dict)

def local_host_recieve_dhcp_message(client, dhcp_dict):
    cctxt = client.prepare(server=dhcp_dict['vm info']['host_id'])
    cctxt.cast({}, 'init_dhcp', dhcp_d = dhcp_dict)

def retrieve_remote_dhcp_data(client, remote):
    for host in remote['dhcp remote hosts']:
        cctxt = client.prepare(server=host['host_id'])
        cctxt.cast({}, 'send_remote_listener_dhcp_data', remote=host)

def check_dnsmasq_process(client, dhcp_dict, host_id):
    cctxt = client.prepare(server=host_id)
    flag = cctxt.call({}, 'dnsmasq_check', dhcp_d = dhcp_dict, host_id = host_id)
    return flag
'''

if __name__ == '__main__':
    main()
