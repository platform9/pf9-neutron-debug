import logging
import coloredlogs
import sys
sys.path.append('../common/')

import init_neutron_client
import discovery

DHCP_SERVER_PREFIX = "DHCP SERVER "
VIF_PREFIX_LEN = 14

logger = logging.getLogger("main_logger")

class LogData:
    def __init__(self):
        self.remote = []
        self.local = {}


    def log_data(self, data_dict, info_dict):

        if (info_dict['checker_type'] == "ICMP" or info_dict['checker_type'] == "FIP"):
            self.log_icmp_and_fip(data_dict, info_dict)
        elif (info_dict['checker_type'] == "SNAT"):
            self.log_snat(data_dict, info_dict)
        elif (info_dict['checker_type'] == "ARP"):
            self.log_arp(data_dict, info_dict)
        elif (info_dict['checker_type'] == "DHCP"):
            self.log_dhcp(data_dict, info_dict)

    def log_icmp_and_fip(self, data_dict, info_dict):
        logger.info("%s PACKET LISTENER DATA -  %s HOST" % (info_dict['checker_type'], info_dict["tag"]))
        if info_dict["path_type"] == "bidirectional":
            self.regular_packet_analysis(data_dict, info_dict)
        logger.info("")

    def log_snat(self, data_dict, info_dict):
        logger.info("SNAT PACKET LISTENER DATA -  %s HOST" % info_dict["tag"])
        if info_dict["tag"] == "VM SOURCE":
            for vif_name, packet_array in data_dict.items():
                if len(packet_array) == 0:
                    logger.error("ERROR: NO ICMP REQUEST OR REPLY FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
		    logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                elif len(packet_array) == 1 and "tap" not in vif_name:
                    if "qr" in vif_name:
                        logger.error("ERROR: LOCAL QROUTER INTERFACE MISSING A REQUEST INBOUND OR OUTBOUND")
                    elif "REQUEST" not in packet_array[0]:
                        logger.error("ERROR: NO ICMP REQUEST FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                    elif "REPLY" not in packet_array[0]:
                        logger.error("ERROR: NO ICMP REPLY FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                    else:
                        logger.error("ERROR: UNKNOWN PACKET ON %s on %s host" % (vif_name, info_dict["tag"]))
		    logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
		else:
                    logger.debug("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
        elif info_dict["tag"] == "SNAT NS":
            self.regular_packet_analysis(data_dict, info_dict)
        logger.info("")

    def log_arp(self, data_dict, info_dict):
        logger.info("VXLAN ARP PACKET LISTENER DATA -  %s HOST" % info_dict["tag"])
    	for vif_name, packet_array in data_dict.items():
    	    logger.debug("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
    	logger.info("")

    def log_dhcp(self, data_dict, info_dict):
        logger.info("DHCP PACKET LISTENER DATA -  %s HOST" % info_dict["tag"])
        if info_dict["tag"] == "VM SOURCE":
            self.local_dhcp = info_dict['local_dhcp']
            self.num_dhcp = info_dict['num_dhcp']
            for vif_name, packet_array in data_dict.items():
                if info_dict['port_id'][:VIF_PREFIX_LEN] in vif_name:
                    if len(packet_array) == 0:
                        logger.error("ERROR: NO DHCP DISCOVER OR OFFER FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                        logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                    elif len(packet_array) == 1:
                        if "DHCPDISCOVER" not in packet_array[0]:
                            logger.error("ERROR: NO DHCP DISCOVER FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                        elif "DHCPOFFER" not in packet_array[0]:
                            logger.error("ERROR: NO DHCP OFFER FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                        logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                    else:
                        if len(packet_array) < self.num_dhcp + 1:
                            logger.error("ERROR: MISSING ONE OR MORE DHCP OFFER MESSAGES ON %s on %s host" % (vif_name, info_dict["tag"]))
                            logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                        else:
                            logger.debug("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                else:
                    if len(packet_array) == 0:
                        logger.error("ERROR: NO DHCP DISCOVER OR OFFER FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                        logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                    elif len(packet_array) == 1:
                        if self.local_dhcp and self.num_dhcp == 1:
                            logger.debug("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                        else:
                            logger.error("ERROR: NO DHCP OFFER FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                            logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                    else:
                        if self.local_dhcp:
                            if len(packet_array) < self.num_dhcp:
                                logger.error("ERROR: MISSING ONE OR MORE DHCP OFFER MESSAGES ON %s on %s host" % (vif_name, info_dict["tag"]))
                                logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                            else:
                                logger.debug("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                        else:
                            if len(packet_array) < self.num_dhcp + 1:
                                logger.error("ERROR: MISSING ONE OR MORE DHCP OFFER MESSAGES ON %s on %s host" % (vif_name, info_dict["tag"]))
                                logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                            else:
                                logger.debug("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
        else:
            for vif_name, packet_array in data_dict.items():
                if len(packet_array) == 0:
                    logger.error("ERROR: NO DHCP DISCOVER OR OFFER FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                    logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                elif len(packet_array) == 1:
                    if "DHCPDISCOVER" not in packet_array[0]:
                        logger.error("ERROR: NO DHCP DISCOVER FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                    elif "DHCPOFFER" not in packet_array[0]:
                        logger.error("ERROR: NO DHCP OFFER FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                    logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
                else:
                    logger.debug("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
        logger.info("")




    def regular_packet_analysis(self, data_dict, info_dict):
        for vif_name, packet_array in data_dict.items():
            if len(packet_array) == 0:
                logger.error("ERROR: NO ICMP REQUEST OR REPLY FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
		logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
            elif len(packet_array) == 1 and "tap" not in vif_name:
                if "REQUEST" not in packet_array[0]:
                    logger.error("ERROR: NO ICMP REQUEST FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                elif "REPLY" not in packet_array[0]:
                    logger.error("ERROR: NO ICMP REPLY FOUND ON %s on %s host" % (vif_name, info_dict["tag"]))
                else:
                    logger.error("ERROR: UNKNOWN PACKET ON %s on %s host" % (vif_name, info_dict["tag"]))
		logger.error("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
            else:
		logger.debug("INTERFACE: " + vif_name + "   " + "PACKET DATA: " + str(packet_array))
