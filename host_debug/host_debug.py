# Host Server for RPC messaging

import time
import sys
import oslo_messaging
import eventlet
import dhcp_local

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
        dhcp_data = dhcp_local.init_dhcp_check(dhcp_d)
        return_to_du(dhcp_data)


def main():

    opts = [cfg.StrOpt('host')]
    CONF.register_opts(opts)
    CONF(sys.argv[1:])
    
    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server=CONF.host, version='2.0', namespace='test')
    server = create_server(CONF, transport, target)

    try:
        server.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping server")


def return_to_du(transport_json):
    
    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server="myserver", version='2.0', namespace='test')
    client = oslo_messaging.RPCClient(transport, target)
    client.cast({}, 'get_dict', d=transport_json)

def create_server(conf, transport, target):
    """
    Create RPC server for handling messaging
    """
    endpoints = [DHCPEndpoint(None)]
    server = oslo_messaging.get_rpc_server(transport, target, endpoints, executor='blocking')
    return server

if __name__ == '__main__':
    main()
