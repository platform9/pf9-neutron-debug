import sys
import oslo_messaging
import eventlet

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF

def main():
    logging.register_options(CONF)
    logging.set_defaults()
    CONF(sys.argv[1:])

    oslo_messaging.set_transport_defaults('myexchange')

    recieve_message()


def recieve_message():
    transport = oslo_messaging.get_transport(CONF,
                     url='rabbit://neutron:4w6IIkHQVeslNjYo@localhost:5673/')
    target = oslo_messaging.Target(topic='myroutingkey', version='2.0',
                                   namespace='test')
    client = oslo_messaging.RPCClient(transport, target)
    r = client.call({}, 'hello_world', name='Neutron Debugger')
    print r



if __name__ == '__main__':
    main()
