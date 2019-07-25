import logging
import sys
sys.path.append('../common/')

import init_neutron_client
import discovery

DHCP_SERVER_PREFIX = "DHCP SERVER "

logging.basicConfig(filename='/var/log/neutron_debug/neutron_debug.log', filemode = 'w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


class LogData:
    def __init__(self):
        self.remote = []
        self.local = {}

    def log_data(self, data_dict):

	if 'arp' in data_dict.keys()[0]:
	    self.log_arp_data_to_file(data_dict, "SOURCE")
        elif 'local host' in data_dict.keys()[0]:
            self.log_data_to_file(data_dict, "LOCAL")
            self.local = data_dict
        elif 'remote host' in data_dict.keys()[0]:
            self.log_data_to_file(data_dict, "REMOTE")
            self.remote.append(data_dict)
	elif 'source' in data_dict.keys()[0]:
	    self.log_icmp_data_to_file(data_dict, "SOURCE")
	elif 'destination' in data_dict.keys()[0]:
	    self.log_icmp_data_to_file(data_dict, "DESTINATION")

    def log_data_to_file(self, data, flag):
        logging.info("DHCP PACKET LISTENER DATA - %s HOST" % flag)
        for k,v in data.items():
            prefix = ""
            if 'dhcp server' in k:
                prefix = DHCP_SERVER_PREFIX
            logging.info(prefix + "INTERFACE: " + str(k.split(":")[1]) + "   " + "PACKET DATA: " + str(v))
        logging.info("")
        return

    def log_icmp_data_to_file(self, data, flag):
	logging.info("ICMP PACKET LISTENER DATA -  %s HOST" % flag)
	for k,v in data.items():
	    logging.info("INTERFACE: " + str(k.split(":")[1]) + "   " + "PACKET DATA: " + str(v))
	logging.info("")
	return
    
    def log_arp_data_to_file(self, data, flag):
	logging.info("VXLAN ARP PACKET LISTENER DATA -  %s HOST" % flag)
	for k,v in data.items():
	    logging.info("INTERFACE: " + str(k.split(":")[1]) + "   " + "PACKET DATA: " + str(v))
	logging.info("")
	return

    def analyze(self):

        # Add the many many conditionals cases for DHCP traffic data_dict
        # One case (DHCP Ports) for PoC for now

        neutron = init_neutron_client.make_neutron_object()

        dhcp_number = discovery.get_dhcp_number(neutron)
