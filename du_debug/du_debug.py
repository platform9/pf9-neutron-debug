# DU Server for RPC messaging

import sys
sys.path.append('../common/')

import time
import oslo_messaging
import eventlet
import init_neutron_client
import dhcp_info

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF

logging.register_options(CONF)
logging.set_defaults()

DONE_WITH_PROCESS = False

# Return Endpoint
class GetHostDataEndpoint(object):
    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server
        self.counter = 0

    def get_dict(self, ctx, d):
        print "_______________RETURNED JSON___________________"
        print d
        self.counter = self.counter + 1
        if self.counter == 2:
            DONE_WITH_PROCESS = True


def main():

    opts = [cfg.StrOpt('host')]
    CONF.register_opts(opts)

    CONF(sys.argv[2:])

    vm_name = sys.argv[1]

    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server='myserver', version='2.0', namespace='test')
    server = create_server(CONF, transport, target)
    client = oslo_messaging.RPCClient(transport, target)

    #server.start()

    eventlet.spawn(server_process, server)

    neutron = init_neutron_client.make_neutron_object()

    # DHCP Dict
    local, remote = dhcp_info.create_dhcp_dict(vm_name, neutron)

    print local
    print remote

    send_to_remote_hosts(client, remote)
    time.sleep(4)
    local_host_recieve_message(client, local)
    time.sleep(2)
    get_remote_data(client, remote)

    time.sleep(4)

def server_process(rpcserver):
    try:
        rpcserver.start()
        for i in range(0,30):
           time.sleep(1)
           if DONE_WITH_PROCESS is True:
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

def send_to_remote_hosts(client, remote):
    for host in remote['dhcp remote hosts']:
        remote_host_recieve_message(client, host)

def local_host_recieve_message(client, dhcp_dict):

    cctxt = client.prepare(server=CONF.host)
    cctxt.cast({}, 'get_dhcp_dict', dhcp_d = dhcp_dict)

def remote_host_recieve_message(client, dhcp_dict):

    print dhcp_dict
    cctxt = client.prepare(server=dhcp_dict['host_id'])
    cctxt.cast({}, 'get_dhcp_dict', dhcp_d = dhcp_dict)

def get_remote_data(client, remote):
    for host in remote['dhcp remote hosts']:
        cctxt = client.prepare(server=host['host_id'])
        cctxt.cast({}, 'get_remote_listener_data', data="")

def stop_server(rpc_server):
    LOG.info('Stopping registry RPC server')
    if rpc_server.listener:
        rpc_server.stop()
        rpc_server.wait()
    else:
        LOG.info('No rpc listener, nothing to stop')


if __name__ == '__main__':
    main()
