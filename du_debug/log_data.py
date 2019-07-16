import logging

DHCP_SERVER_PREFIX = "DHCP SERVER "

logging.basicConfig(filename='/var/log/neutron_debug/dhcp.log', filemode = 'w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def log_data(data_dict):

    if 'local host' in data_dict.keys()[0]:
        log_data_to_file(data_dict, "LOCAL")
    else:
        log_data_to_file(data_dict, "REMOTE")


def log_data_to_file(data, flag):
    logging.info("DHCP PACKET LISTENER DATA - %s HOST" % flag)
    for k,v in data.items():
        prefix = ""
        if 'dhcp server' in k:
            prefix = DHCP_SERVER_PREFIX
        logging.info(prefix + "INTERFACE: " + str(k.split(":")[1]) + "   " + "PACKET DATA: " + str(v))
    logging.info("")
    return
