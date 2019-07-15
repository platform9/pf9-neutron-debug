# Host Server for RPC messaging

import sys
sys.path.append('../common/')

import time
import oslo_messaging
import eventlet
import dhcp_local
import dhcp_remote

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

    def get_dhcp_dict(self, ctx, dhcp_d):
        print "__________________"
	print dhcp_d
	print "__________________"
	if "dhcp local host" in dhcp_d.keys():
            print "THERE"
	    self.dhcp_local_data = dhcp_local.init_dhcp_check(dhcp_d)
            return_to_du(self.dhcp_local_data)
        elif "dhcp remote host" in dhcp_d.keys():
	    self.listeners, self.thread = dhcp_remote.init_dhcp_check(dhcp_d)


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
