import struct
from scapy import all as scapy
from pprint import pprint

DEV_NAME_LEN = 14
QBR_DEV_PREFIX = "qbr"
QVB_DEV_PREFIX = "qvo"
DHCP_MESSATE_TYPE = ['', 'DHCPDISCOVER', 'DHCPOFFER', 'DHCPREQUEST',
    'DHCPDECLINE', 'DHCPACK', 'DHCPNAK', 'DHCPRELEASE']
ICMP_MESSAGE_TYPE = {0:'REPLY',8:'REQUEST', 3:'DEST_UNREACHABLE'}

DHCP_NS_PREFIX = 'qdhcp-'
ARP_OP_TYPE = ['', 'REQUEST', 'REPLY']

class ScapyDriver(object):

    def send_icmp_on_interface(self, interface_name,src_mac, dst_mac, src_ip, dst_ip, payload):
        """Send ICMP Request over qbr device.
        """
        src_ip = str(src_ip)
        dst_ip = str(dst_ip)
        src_mac = str(src_mac)
        dst_mac = str(dst_mac)
        payload = str(payload)
        interface_name = str(interface_name)
        ip = scapy.IP(src=src_ip,dst=dst_ip)
        icmp = scapy.ICMP()
        packet = scapy.Ether(src=src_mac, dst=dst_mac)/ ip / icmp / scapy.Raw(load=payload)
        scapy.sendp(packet, iface=interface_name)

    def send_dhcp_over_qbr(self, qbr_device, port_mac):
        """Send DHCP Discovery over qbr device.
        """
        ethernet = scapy.Ether(dst='ff:ff:ff:ff:ff:ff',
                               src=port_mac, type=0x800)
        ip = scapy.IP(src='0.0.0.0', dst='255.255.255.255')
        udp = scapy.UDP(sport=68, dport=67)
        port_mac_t = tuple(map(lambda x: int(x, 16), port_mac.split(':')))

        hw = struct.pack('6B', *port_mac_t)
        bootp = scapy.BOOTP(chaddr=hw, flags=1)
        dhcp = scapy.DHCP(options=[("message-type", "discover"), "end"])
        packet = ethernet / ip / udp / bootp / dhcp
        scapy.sendp(packet, iface=qbr_device)

    def send_arp_on_interface(self, interface_name, src_mac, src_ip, dst_ip):
        """Send ARP Request over qbr device.
        """
        ethernet = scapy.Ether(dst='ff:ff:ff:ff:ff:ff',
                               src=src_mac)
        arp = scapy.ARP(op="who-has", hwsrc=src_mac, psrc=src_ip, pdst=dst_ip)
        packet = ethernet / arp
        scapy.sendp(packet, iface=interface_name)


    def get_dhcp_mt(self, ether_packet):
        """Pick out DHCP Message Type from buffer.
        """
        dhcp_packet = ether_packet[scapy.DHCP]
        message = dhcp_packet.options[0]
        return DHCP_MESSATE_TYPE[message[1]], ether_packet.src, ether_packet.dst

    def get_icmp_mt(self, ether_packet):
        """Pick out ICMP Message Type from buffer.
        """
        icmp_packet = ether_packet[scapy.ICMP]
        icmp_type = icmp_packet.type
        if icmp_type in ICMP_MESSAGE_TYPE:
            return ICMP_MESSAGE_TYPE[icmp_type], ether_packet.src, ether_packet.dst
        return "UNKNOWN"

    def get_arp_op(self, ether_packet):
        """Pick out ARP Message Type from buffer.
        """
        arp_packet = ether_packet[scapy.ARP]
        return ARP_OP_TYPE[arp_packet.op], ether_packet.src, ether_packet.dst
