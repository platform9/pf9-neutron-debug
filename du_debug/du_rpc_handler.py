import sys
sys.path.append('../common/')
sys.path.append('./dhcp/')
sys.path.append('./icmp/')
sys.path.append('./api')

import time
import oslo_messaging
import eventlet
import pdb

from oslo_config import cfg
from oslo_log import log as logging

oslo_messaging.set_transport_defaults('myexchange')

class RPCClientObject:

    def __init__(self, conf):

        self.transport = oslo_messaging.get_transport(conf)
        self.target = oslo_messaging.Target(topic='myroutingkey', server='myserver', version='2.0', namespace='test')
        self.client = oslo_messaging.RPCClient(self.transport, self.target)

    def get_rpc_client(self):
        return self.client


    def listen_on_host(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        cctxt.cast({}, 'set_port_listeners', listener_dict = listen_dict)

    def source_inject(self, inject_dict):

        cctxt = self.client.prepare(server=inject_dict['host_id'])
        cctxt.cast({}, 'inject_icmp_packet', inject_dict = inject_dict)

    def retrieve_listener_data(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        cctxt.cast({}, 'send_listener_data', listener_dict = listen_dict)
