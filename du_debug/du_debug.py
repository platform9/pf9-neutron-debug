# Host Server for RPC messaging

import sys
import oslo_messaging
import eventlet

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF

grp = cfg.OptGroup('mygroup')
CONF.register_group(grp)

logging.register_options(CONF)
logging.set_defaults()


class TestEndpoint(object):
    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server

    def hello_world(self, ctx, name):
        return "Hello my name is %s!" % (name)


def main():

    CONF(sys.argv[1:])

    server = create_server(CONF)
    server.start()
    print 'Running RPC server via RabbitMQ...'
    server.wait()
    stop_server(server)


def create_server(conf):
    """
    Create RPC server for handling messaging
    """
    oslo_messaging.set_transport_defaults('myexchange')
    transport = oslo_messaging.get_transport(conf)
    target = oslo_messaging.Target(topic='myroutingkey', server='myserver')
    endpoints = [TestEndpoint(None)]
    server = oslo_messaging.get_rpc_server(transport, target, endpoints,
                                      executor='eventlet')
    return server


def stop_server(rpc_server):
    LOG.info('Stopping registry RPC server')
    if rpc_server.listener:
        rpc_server.stop()
        rpc_server.wait()
    else:
        LOG.info('No rpc listener, nothing to stop')


if __name__ == '__main__':
    main()
