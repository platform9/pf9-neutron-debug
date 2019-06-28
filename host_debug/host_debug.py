import sys
from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF



def main():
    logging.register_options(CONF)
    logging.set_defaults()
    CONF(sys.argv[1:])

    oslo.messaging.set_transport_defaults('myexchange')

    recieve_message()


def recieve_message():
    transport = oslo.messaging.get_transport(CONF,
                     url='<insert DU URL>')
    target = oslo.messaging.Target(topic='myroutingkey', version='2.0',
                                   namespace='test')
    client = oslo.messaging.RPCClient(transport, target)
    r = client.call({}, 'hello_world', name='Neutron Debugger')
    print r



if __name__ == '__main__':
    main()
