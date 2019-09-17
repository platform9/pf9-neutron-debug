import pcap
import constants

class PcapDriver(object):

    def setup_listener(self, iface, filter, timeout=10):
        """
        Set up pcap listener on given interface for a brief period of time
        """

        listener = pcap.pcap(iface, timeout_ms=timeout * 1000)
        listener.setfilter(filter)
        listener.setnonblock(True)
        return listener

    def set_nonblock(self, listener):
        listener.setnonblock(True)
