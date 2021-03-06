import sys
sys.path.append('../../common/')

import pdb
import os
import init_neutron_client
import discovery
import logging
import coloredlogs

logger = logging.getLogger("main_logger")

def run_du_static_checks(vm_name, neutron):
    """
    Runs heartbeat checks on hosts to see if ports are up
    """

    vm_name = discovery.vmname_parse(vm_name)
    vm_port_dict = discovery.get_port_dict(vm_name, neutron)
    network_id = vm_port_dict['network_id']
    host_id = vm_port_dict['binding:host_id']
    dhcp_ports = discovery.get_all_dhcp_ports(network_id, neutron)

    vm_host_code = discovery.heartbeat_host(host_id, neutron)
    vm_code = discovery.heartbeat_port(vm_port_dict)

    host_error_dict = dict()
    for dhcp_port in dhcp_ports:
        dhcp_host_code = discovery.heartbeat_host(dhcp_port['binding:host_id'], neutron)
        host_error_dict[dhcp_port['binding:host_id']] = dhcp_host_code

    dhcp_error_dict = dict()
    for dhcp_port in dhcp_ports:
        dhcp_code = discovery.heartbeat_port(dhcp_port)
        dhcp_error_dict[dhcp_port['binding:host_id']] = dhcp_code

    fail_code = diagnose_error(vm_host_code, vm_code, host_error_dict, dhcp_error_dict)
    return fail_code

def diagnose_error(vm_host_code, vm_code, host_error_dict, dhcp_error_dict):
    """
    Based on error code from hosts, determine the error message
    """

    if vm_host_code == 1:
        logger.info("VM HOST is down, unable to run DHCP traffic tests\n")
        return 1
    if vm_code == 1:
        logger.info("VM Port is down, unable to run DHCP traffic tests\n")
        return 1

    dhcp_host_error = 0
    for i_d,code in host_error_dict.items():
        if code == 1:
            logger.info("DHCP HOST %s is down, unable to run DHCP traffic tests\n" % (i_d))
            dhcp_host_error = 1
    if dhcp_host_error:
        return 1

    dhcp_server_error = 0
    for i_d,code in dhcp_error_dict.items():
        if code == 1:
            logger.info("DHCP SERVER Port %s is down, unable to run DHCP traffic tests\n" % (i_d))
            dhcp_host_error = 1
    if dhcp_host_error:
        return 1

    logger.info("HEARTBEAT tests look OK, ready to move on")
    logger.info("")
    return 0
