import logging

DHCP_SERVER_PREFIX = "DHCP SERVER "

logging.basicConfig(filename='/var/log/neutron_debug/dhcp_info.log', filemode = 'w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def log_data(data_dict):

    if "local host" in data_dict.keys():
        log_local_data(data_dict)
    else:
        log_remote_data(data_dict)


def log_local_data(data):
    logging.info("DHCP PACKET LISTENER DATA FOR LOCAL HOST")
    for k,v in data.items():
        prefix = ""
        if "dhcp server" in k:
            prefix = DHCP_SERVER_PREFIX
        logging.info(prefix + "INTERFACE: " + str(k.split(":")[1]) + "   " + "PACKET DATA: " + str(v))
    logging.info("")
    return

def log_remote_data(data):
    logging.info("DHCP PACKET LISTENER DATA FOR REMOTE HOST")
    for k,v in data.items():
        logging.info("INTERFACE: " + str(k.split(":")[1]) + "   " + "PACKET DATA: " + str(v))
    return
