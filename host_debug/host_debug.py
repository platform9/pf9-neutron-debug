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

class ResponseEndpoint(object):
    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server

    def hello_back(self, ctx, name):
        print "Hello back! I am %s." % (name)

def main():

    CONF(sys.argv[1:])
    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server='myserver', version='2.0', namespace='test')
    server = create_server(CONF, transport, target)
    client = oslo_messaging.RPCClient(transport, target)

    recieve_message(client)
    try:
        server.start()
        time.sleep(6)
    except KeyboardInterrupt:
        print("Stopping server")
    

def create_server(conf, transport, target):
    """
    Create RPC server for handling messaging
    """
    endpoints = [ResponseEndpoint(None)]
    server = oslo_messaging.get_rpc_server(transport, target, endpoints, executor='blocking')
    return server

def recieve_message(client):
    client.cast({}, 'hello_world', name='the DU')
    



if __name__ == '__main__':
    main()
