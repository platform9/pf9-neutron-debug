# DU Server for RPC messaging and HTTP requests

import sys
sys.path.append('../common/')
sys.path.append('./dhcp/')
sys.path.append('./icmp/')
sys.path.append('./api')
sys.path.append('./arp')
sys.path.append('./fip')
sys.path.append('./snat')

import time
import oslo_messaging
import eventlet
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

# Return Endpoint
class GetHostDataEndpoint(object):
    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server
        self.log_info = log_data.LogData()

    def recieve_dict(self, ctx, data, info):
        """
        Retrieve packet data from host to log
        """
        self.log_info.log_data(data, info)

    def get_message(self, ctx, message):
        """
        Retrieve message from host to log
        """
        logs.info(message)

def main():

    CONF(sys.argv[1:])

    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server='myserver', version='2.0', namespace='test')
    server = create_server(CONF, transport, target)

    # Reset RPC server before starting
    server.start()
    server.stop()
    server.wait()

    # Thread for RPC server
    server_thread = threading.Thread(target=server_process, args=(server,))
    server_thread.daemon = True
    server_thread.start()

    start_wsgi_server()

def start_wsgi_server():
    """
    Uses WSGI to start a Flask server and listen for requests
    """
    paste_file = CONF.paste_ini
    wsgi_app = loadapp('config:%s' % paste_file, "main")
    listen_port = CONF.listen_port
    wsgi.server(eventlet.listen(('', listen_port)), wsgi_app)

def server_process(rpcserver):
    """
    Keeps RPC server on until KeyboardInterrupt
    """
    try:
        rpcserver.reset()
        rpcserver.start()
        print("Server Starting...")
        while True:
           time.sleep(1)
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


if __name__ == '__main__':
    main()
