# DU Server for RPC messaging

import time
import sys
import oslo_messaging
import eventlet
import init_neutron_client

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF

logging.register_options(CONF)
logging.set_defaults()

class TestEndpoint(object):
    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server

    def hello_world(self, ctx, name):
        print "Hello my name is %s!" % (name)

def main():

    CONF(sys.argv[2:])

    vm_name = sys.argv[1]

    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server='myserver', version='2.0', namespace='test')
    server = create_server(CONF, transport, target)
    client = oslo_messaging.RPCClient(transport, target)

    neutron = init_neutron_client.make_neutron_object()

    # DHCP Dict
    d = dhcp_info.create_dhcp_dict(vm_name, neutron)

    recieve_message(client, d)

    #try:
    #    server.start()
    #    time.sleep(6)
    #except KeyboardInterrupt:
    #    print("Stopping server")

def create_server(conf, transport, target):
    """
    Create RPC server for handling messaging
    """
    endpoints = [TestEndpoint(None)]
    server = oslo_messaging.get_rpc_server(transport, target, endpoints, executor='blocking')
    return server

def recieve_message(client, dhcp_dict):
    client.cast({}, 'get_dhcp_dict', dhcp_d = dhcp_dict)

def stop_server(rpc_server):
    LOG.info('Stopping registry RPC server')
    if rpc_server.listener:
        rpc_server.stop()
        rpc_server.wait()
    else:
        LOG.info('No rpc listener, nothing to stop')


if __name__ == '__main__':
    main()
