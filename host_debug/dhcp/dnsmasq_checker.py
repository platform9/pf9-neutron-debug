import os


def init_dnsmasq_check(dhcp_dict):
    error_code = analyze_dnsmasq(dhcp_dict)
    message = diagnose_dnsmasq(error_code, dhcp_dict)
    return message

def analyze_dnsmasq(dhcp_dict):

    process_flag = False
    os.system("ps ax | grep dnsmasq | grep % > dnsmasq.txt" % (dhcp_dict['network_id']))
    with open('dnsmasq.txt') as file
        output = file.readlines()
    for line in output:
        if "dnsmasq" in line:
            process_flag = True
            break

    if not process_flag:
        return 1

    instance_flag = False
    with open("var/opt/pf9/neutron/dhcp/%s/host" % (dhcp_dict['network_id'])) as file:
        output = file.readlines()
    for line in output
        if dhcp_dict['mac_address'] in line and dhcp_dict['ip_address'] in line:
            instance_flag = True
            break

    if not instance_flag:
        return 2

    return 0

def diagnose_dnsmasq(error_code, dhcp_dict):

    if error_code == 0:
        message = "CODE 0: Successfully identified dnsmasq process for host %s and found MAC and IP for source VM of interest in dnsmasq" % (dhcp_dict['host_id'])
    elif error_code == 1:
        message = "CODE 1: No dnsmasq process exists for host %s" % (dhcp_dict['host_id'])
    else:
        message = "CODE 2: Successfully identified dnsmasq process for host %s, but not for source VM of interest" % (dhcp_dict['host_id'])
    return message
