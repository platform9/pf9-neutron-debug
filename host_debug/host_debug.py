# Host Server for RPC messaging

import sys
sys.path.append('../common/')
sys.path.append('./dhcp/')

import time
import oslo_messaging
import eventlet
import dhcp_local
import dhcp_remote
import dnsmasq_checker

import scapy_driver
import pcap_driver

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF

logging.register_options(CONF)
logging.set_defaults()

class DHCPEndpoint(object):
    import scapy_driver
    import pcap_driver

    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server
	self.pcap = pcap_driver.PcapDriver()
	self.scapy = scapy_driver.ScapyDriver()


    def get_remote_listener_data(self, ctx, remote):
        self.thread.join()
        dhcp_remote_data = dhcp_remote.get_sniff_result(self.listeners, self.scapy.get_dhcp_mt)
        dhcp_remote_data = dhcp_remote.merge_data(dhcp_remote_data, remote)
        return_to_du(dhcp_remote_data)

    def init_dhcp(self, ctx, dhcp_d):
	if "dhcp local host" in dhcp_d.keys():
	   self.dhcp_local_data = dhcp_local.init_dhcp_check(dhcp_d)
           return_to_du(self.dhcp_local_data)
        elif "dhcp remote host" in dhcp_d.keys():
	   self.listeners, self.thread = dhcp_remote.init_dhcp_check(dhcp_d)

    def dnsmasq_check(self, ctx, dhcp_d, host_id):

        message = dnsmasq_checker.init_dnsmasq_check(dhcp_d, host_id)
        message_to_du(message)

class ICMPEndpoint(object):

    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server

    def init_icmp(self, ctx, icmp_d):
	return
        

def main():

    opts = [cfg.StrOpt('host')]
    CONF.register_opts(opts)
    CONF(sys.argv[1:])

    oslo_messaging.set_transport_defaults('myexchange')
    global transport
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server=CONF.host, version='2.0', namespace='test')

    global du_target
    du_target = oslo_messaging.Target(topic='myroutingkey', server="myserver", version='2.0', namespace='test')

    server = create_server(CONF, transport, target)

    try:
        server.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping server")


def return_to_du(transport_json):

    client = oslo_messaging.RPCClient(transport, du_target)
    client.cast({}, 'recieve_dhcp_dict', d=transport_json)

def message_to_du(message):

    client = oslo_messaging.RPCClient(transport, du_target)
    client.cast({}, 'get_message', message=message)

def create_server(conf, transport, target):
    """
    Create RPC server for handling messaging
    """
    endpoints = [DHCPEndpoint(None)]
    server = oslo_messaging.get_rpc_server(transport, target, endpoints, executor='blocking')
    return server

if __name__ == '__main__':
    main()
