import logging

def log_data(data_dict):

    if "local host" in data_dict.keys():
        log_local_data(data_dict)
    else:
        log_remote_data(data_dict)


def log_local_data(data):
    logging.info("DHCP PACKET LISTENER DATA FOR LOCAL HOST")
    for k,v in data.items():
        logging.info("INTERFACE: " + k.split(":")[1] + "   " + "PACKET DATA: " + v)
    logging.info("")
    return

def log_remote_data(data):
    logging.info("DHCP PACKET LISTENER DATA FOR REMOTE HOST")
    for k,v in data.items():
        logging.info("INTERFACE: " + k.split(":")[1] + "   " + "PACKET DATA: " + v)
    return
