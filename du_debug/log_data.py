import logging

def log_data(data_dict):
    logging.basicConfig(filename='debug_info.log', filemode = 'w', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S',
                        level=logging.INFO)
    if "local host" in data_dict.keys():
        log_local_data(data_dict)
    else:
        log_remote_data(data_dict)


def log_local_data(data):
    logging.info("")
    return

def log_remote_data(data):

    return
