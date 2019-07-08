# Host Server for RPC messaging

import time
import sys
import oslo_messaging
import eventlet

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF

logging.register_options(CONF)
logging.set_defaults()

class DHCPEndpoint(object):
    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server

    def get_dhcp_dict(self, ctx, dhcp_d):
	print dhcp_d

def main():
    
    opts = [cfg.StrOpt('host')]
    CONF.register_opts(opts)


    CONF(sys.argv[1:])
    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server=CONF.host, version='2.0', namespace='test')
    server = create_server(CONF, transport, target)
    client = oslo_messaging.RPCClient(transport, target)

    try:
        server.start()
        while True:    
            time.sleep(1)
        #time.sleep(4)
        #recieve_message(client)
    except KeyboardInterrupt:
        print("Stopping server")

    #recieve_message(client)

def create_server(conf, transport, target):
    """
    Create RPC server for handling messaging
    """
    endpoints = [DHCPEndpoint(None)]
    server = oslo_messaging.get_rpc_server(transport, target, endpoints, executor='blocking')
    return server

def recieve_message(client):
    client.cast({}, 'hello_world', name='the DU')




if __name__ == '__main__':
    main()
