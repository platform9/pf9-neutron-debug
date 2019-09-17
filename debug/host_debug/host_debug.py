# Host Server for RPC messaging

import sys
sys.path.append('../common/')
sys.path.append('./dhcp/')

import time
import oslo_messaging
import eventlet
import dnsmasq_checker

import scapy_driver
import pcap_driver
import set_listeners
import set_ns_listeners

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF

logging.register_options(CONF)
logging.set_defaults()

class CheckerEndpoint(object):
    """
    RPC endpoint that takes requests from the DU.
    Pairs with du_rpc_handler.py
    """

    import scapy_driver
    import pcap_driver

    target = oslo_messaging.Target(namespace='test', version='2.0')

    def __init__(self, server):
        self.server = server
        self.pcap = pcap_driver.PcapDriver()
        self.scapy = scapy_driver.ScapyDriver()
        self.listener_obj_dict = dict()
        self.ns_listener_obj_dict = dict()

    def dnsmasq_check(self, ctx, dhcp_d, host_id):
        """
        Runs dnsmasq process check and returns result
        """

        message = dnsmasq_checker.init_dnsmasq_check(dhcp_d, host_id)
        return message


    def set_port_listeners(self, ctx, listener_dict):
        """
        Sets listeners on ports from listener_dict
        """

        set_listen_obj = set_listeners.SetListener(listener_dict)
        set_listen_obj.init_listeners()
        self.listener_obj_dict[listener_dict['port_id']] = set_listen_obj
        time.sleep(2)

    def set_ns_port_listeners(self, ctx, listener_dict):
        """
        Sets listeners on ports from listener_dict.
        Uses tcmpdump manually since ports in this listener_dict are part of a namespace
        """

        set_ns_listen_obj = set_ns_listeners.SetNsListener(listener_dict)
        set_ns_listen_obj.init_listeners()
        self.ns_listener_obj_dict[listener_dict['port_id']] = set_ns_listen_obj
        time.sleep(2)

    def inject_dhcp_packet(self, ctx, inject_dict):
        """
        Inject DHCP packet on VM
        """

        self.scapy.send_dhcp_over_qbr(inject_dict['inject_port'], inject_dict['src_mac_address'])
        time.sleep(1)

    def inject_icmp_packet(self, ctx, inject_dict):
        """
        Inject ICMP packet on VM
        """

        self.scapy.send_icmp_on_interface(inject_dict['inject_port'], inject_dict['src_mac_address'], inject_dict['dest_mac_address'], inject_dict['src_ip_address'], inject_dict['dest_ip_address'], inject_dict['payload'])
        time.sleep(1)

    def inject_arp_packet(self, ctx, inject_dict):
        """
        Inject ARP packet on VM
        """

        self.scapy.send_arp_on_interface(inject_dict['inject_port'], inject_dict['src_mac_address'], inject_dict['src_ip_address'], inject_dict['dest_ip_address'])
        time.sleep(1)

    def send_listener_data(self, ctx, listener_dict):
        """
        Sends port listener packet data back to the DU
        """

        checker_data = self.listener_obj_dict[listener_dict['port_id']].collect_data()
        log_to_du(checker_data, listener_dict)
        return checker_data

    def send_ns_listener_data(self, ctx, listener_dict):
        """
        Sends namespace port listener packet data back to the DU
        """

        checker_data = self.ns_listener_obj_dict[listener_dict['port_id']].collect_data()
        log_to_du(checker_data, listener_dict)
        return checker_data

def main():

    opts = [cfg.StrOpt('host')]
    CONF.register_opts(opts)
    CONF(sys.argv[1:])

    # Creates global transport and target variables
    oslo_messaging.set_transport_defaults('myexchange')
    global transport
    transport = oslo_messaging.get_transport(CONF)
    target = oslo_messaging.Target(topic='myroutingkey', server=CONF.host, version='2.0', namespace='test')

    global du_target
    du_target = oslo_messaging.Target(topic='myroutingkey', server="myserver", version='2.0', namespace='test')

    # Creates RPC server
    server = create_server(CONF, transport, target)

    server.start()
    server.stop()
    server.wait()

    # Runs RPC server until KeyboardInterrupt
    try:
        server.reset()
        server.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        server.wait()
        print("Stopping server")


def log_to_du(transport_json, information_json):
    """
    Sends data to DU to log
    """

    client = oslo_messaging.RPCClient(transport, du_target)
    client.cast({}, 'recieve_dict', data=transport_json, info=information_json)

def message_to_du(message):
    """
    Sends message back to DU for dnsmasq
    """

    client = oslo_messaging.RPCClient(transport, du_target)
    client.cast({}, 'get_message', message=message)

def create_server(conf, transport, target):
    """
    Create RPC server for handling messaging
    """
    endpoints = [CheckerEndpoint(None)]
    server = oslo_messaging.get_rpc_server(transport, target, endpoints, executor='blocking')
    return server

if __name__ == '__main__':
    main()
