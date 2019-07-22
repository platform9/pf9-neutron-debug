import pcap
import constants
#import scapy_checker as sc

class PcapDriver(object):

    def setup_listener(self, iface, filter, timeout=10):
        listener = pcap.pcap(iface, timeout_ms=timeout * 1000)
        listener.setfilter(filter)
        listener.setnonblock(True)
        return listener

    #def setup_listener_on_comp(self, port_id, filter):
    #    vif_dict = dcp.get_vif_names(port_id)
    #    vif_devices = [vif_dict["tap"], vif_dict["qvb"], vif_dict["qbr"], vif_dict["qvo"]]
    #    return map(lambda vif: self.setup_listener(vif, filter), vif_devices)

    def set_nonblock(self, listener):
        listener.setnonblock(True)
