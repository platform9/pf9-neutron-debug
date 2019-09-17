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
    """
    This class can be instantiated as an object that contains every RPC call needed for this service
    """

    def __init__(self, conf):

        self.transport = oslo_messaging.get_transport(conf)
        self.target = oslo_messaging.Target(topic='myroutingkey', server='myserver', version='2.0', namespace='test')
        self.client = oslo_messaging.RPCClient(self.transport, self.target)

    def get_rpc_client(self):
        return self.client

    def check_dnsmasq_process(self, dhcp_dict, host_id):
        cctxt = self.client.prepare(server=host_id)
        flag = cctxt.call({}, 'dnsmasq_check', dhcp_d = dhcp_dict, host_id = host_id)
        return flag

    # Set listeners on host
    def listen_on_host(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        cctxt.cast({}, 'set_port_listeners', listener_dict = listen_dict)

    def listen_ns_on_host(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        cctxt.cast({}, 'set_ns_port_listeners', listener_dict = listen_dict)

    # Inject packet type on VM
    def source_dhcp_inject(self, inject_dict):

        cctxt = self.client.prepare(server=inject_dict['host_id'])
        cctxt.cast({}, 'inject_dhcp_packet', inject_dict = inject_dict)

    def source_icmp_inject(self, inject_dict):

        cctxt = self.client.prepare(server=inject_dict['host_id'])
        cctxt.cast({}, 'inject_icmp_packet', inject_dict = inject_dict)

    def source_arp_inject(self, inject_dict):

        cctxt = self.client.prepare(server=inject_dict['host_id'])
        cctxt.cast({}, 'inject_arp_packet', inject_dict = inject_dict)

    # Retrieve packet data from hosts
    def retrieve_listener_data(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        response_dict = cctxt.call({}, 'send_listener_data', listener_dict = listen_dict)
        return response_dict

    def retrieve_ns_listener_data(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        response_dict = cctxt.call({}, 'send_ns_listener_data', listener_dict = listen_dict)
        return response_dict
