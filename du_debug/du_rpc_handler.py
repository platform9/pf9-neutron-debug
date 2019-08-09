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

    # DHCP RPC Message Functions
    def send_dhcp_to_remote_hosts(self, remote):
        for host in remote['dhcp remote hosts']:
            self.remote_host_recieve_dhcp_message(host)

    def remote_host_recieve_dhcp_message(self, dhcp_dict):
        cctxt = self.client.prepare(server=dhcp_dict['host_id'])
        cctxt.cast({}, 'init_dhcp', dhcp_d = dhcp_dict)


    def local_host_recieve_dhcp_message(self, dhcp_dict):
        cctxt = self.client.prepare(server=dhcp_dict['vm info']['host_id'])
        local_dhcp_response = cctxt.call({}, 'init_dhcp', dhcp_d = dhcp_dict)
        return local_dhcp_response

    def retrieve_remote_dhcp_data(self, remote):
        response_list = []
        for host in remote['dhcp remote hosts']:
            cctxt = self.client.prepare(server=host['host_id'])
            dhcp_response = cctxt.call({}, 'send_remote_listener_dhcp_data', remote=host)
            response_list.append(dhcp_response)
        return response_list

    def check_dnsmasq_process(self, dhcp_dict, host_id):
        cctxt = self.client.prepare(server=host_id)
        flag = cctxt.call({}, 'dnsmasq_check', dhcp_d = dhcp_dict, host_id = host_id)
        return flag



    # ALl other RPC functions
    def listen_on_host(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        cctxt.cast({}, 'set_port_listeners', listener_dict = listen_dict)

    def listen_ns_on_host(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        cctxt.cast({}, 'set_ns_port_listeners', listener_dict = listen_dict)

    def source_icmp_inject(self, inject_dict):

        cctxt = self.client.prepare(server=inject_dict['host_id'])
        cctxt.cast({}, 'inject_icmp_packet', inject_dict = inject_dict)

    def source_arp_inject(self, inject_dict):

        cctxt = self.client.prepare(server=inject_dict['host_id'])
        cctxt.cast({}, 'inject_arp_packet', inject_dict = inject_dict)

    def retrieve_listener_data(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        response_dict = cctxt.call({}, 'send_listener_data', listener_dict = listen_dict)
        return response_dict

    def retrieve_ns_listener_data(self, listen_dict):

        cctxt = self.client.prepare(server=listen_dict['host_id'])
        response_dict = cctxt.call({}, 'send_ns_listener_data', listener_dict = listen_dict)
        return response_dict
