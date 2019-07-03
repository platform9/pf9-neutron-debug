import sys
sys.path.append('../common/')

import subprocess
#import scapy_checker as sc
import os_info
#import checker as ck
import ConfigParser
import phy_int
import os
import getpass
#import json_logger
#import json

DEV_PREFIX = 14

class HostChecker:

    def __init__(self, test_name):
        self.testname = test_name

    def check(self):
        return 0, ""

    def run(self):
        error_code, error_msg = self.check()
        if error_code == 0:
            error_msg = "OK"
        self.Log(self.testname)
        self.Log(error_msg)
        self.Log(error_code)
        #ck.Checker.jLog.log_test(self.testname, error_code, error_msg)

    def apply_fix_action(self,error_code):
        return ""

    def run_diagnose(self):
        self.check()
        return self.fix_action()

    def Log(self, msg):
        print msg


    def run_cmd(self,cmd):
        #output = subprocess.check_output(cmd)
        #output = output.split('\n')
        output = []
        with open(cmd) as f:
            output = f.readlines()
        return output


class DHCPChecker(HostChecker):
    def __init__(self, phy_port,  port_id, src_mac, net_type):
        HostChecker.__init__(self, "DHCPCheck")
        self.phy = str(phy_port)
        self.src_mac = str(src_mac)
        self.port_id = str(port_id)
        self.net_type = str(net_type)

    def check(self):
        self.Log('-'*50)
        self.Log("Checking for DHCP activity")
        try:
            check_result = init_dhcp_check(self.phy, self.port_id,\
                self.src_mac, self.net_type)
        except Exception as e:
            check_result = "One of the port in IP plumbing is missing\n" + str(e)
            return 1, check_result
        return check_result

    def init_dhcp_check(phy_port, port_id, src_mac, net_type):
        vif_names = get_vif_names(port_id)
        vif_names[phy_port] = phy_port
        reply = check_dhcp(vif_names, src_mac)
        return check_dhcp_result_sender(vif_names, reply, phy_port)

    def concat_vif_name(device_name, port_id):
    	full_name = device_name + port_id
    	return full_name[:VIF_PREFIX_LEN]

    def get_vif_names(port_id):
        vif_names = {}
        tap_device = concat_vif_name("tap", port_id)
        qvb_device = concat_vif_name("qvb", port_id)
        qbr_device = concat_vif_name("qbr", port_id)
        qvo_device = concat_vif_name("qvo", port_id)

        vif_names = {"tap":tap_device, "qvb":qvb_device,
                    "qvo":qvo_device, "qbr":qbr_device}
        return vif_names

    def check_dhcp(vif_names, src_mac, net_type='vlan', is_sender=True):
        #try:
        pcap = pcap_driver.PcapDriver()
        scapy = scapy_driver.ScapyDriver()

        filter = "udp port (67 or 68) and ether host %s" % src_mac

        if cmp(net_type, 'vlan'):
            #TODO: Difference with other type of network?
            raise Exception("network type %s not supported." % net_type)

            listeners = []
            for k,v in vif_names.items():
                listeners.append(pcap.setup_listener(v, filter))

        #sending icmp echo on interface
        #print vif_names["qbr"]

        if is_sender:
            scapy.send_dhcp_over_qbr(vif_names["qbr"], src_mac)
            time.sleep(1)
        else:
            time.sleep(10)

        data = get_sniff_result(listeners, scapy.get_dhcp_mt)
        return data


    def apply_fix_action(self,err_code):
        return "Unable to fix"

    def check_dhcp_result_sender(vif_names, dhcp_result,phy_int):
        if "DHCPOFFER" in dhcp_result[vif_names["tap"]]:
            return 0, "success"

        if "DHCPOFFER" in dhcp_result[vif_names["qvb"]]:
            return 1, "reply is blocked by linux bridge, \
                   check inbound security rule"

        #TODO: Make sure the outbound packet imply inbound packet
        if "DHCPDISCOVER" in dhcp_result[vif_names[phy_int]]:
            return 2, "request leaves the physical host, check for configuration of other hosts/network"

        if "DHCPDISCOVER" in dhcp_result[vif_names["qvo"]]:
            return 3, "check for ovs configurations"

        if "DHCPDISCOVER" in dhcp_result[vif_names["qvb"]]:
            return 4, "check for veth-pair"
        return 5, "check for outbound security rules"

    def get_sniff_result(listeners,handler):
        data = dict()
        for listener in listeners:
            vif_pre = listener.name
            data[vif_pre] = []
            for packet in listener.readpkts():
                icmp_type = handler(str(packet[1]))
                if icmp_type is not None:
                    data[vif_pre].append(icmp_type)
        return data

def get_host_id():
    config = ConfigParser.ConfigParser()
    config.read('/app/host_id.conf')
    return config.get('hostagent','host_id')

if __name__ == "__main__":
    vid = sys.argv[1]
    #open('check.log', 'w').close()
    phy_interface = phy_int.get_phy_interface()
    #phy_interface = "ens32"
    info_global = os_info.GlobalOSInfo()
    info_vm_ck = os_info.VMOSInfo(info_global,vid)
    port_ids = info_vm_ck.get_port_info('id')

    vm_ids = info_global.get_server_id_all()
    vm_info_all = {}

    for vid in vm_ids:
        info_vm = os_info.VMOSInfo(info_global,vid)
        vm_info_all[vid] = info_vm

    host_info = os_info.HostInfo(info_global, vm_info_all)
    host_id = get_host_id()

    vm_info = host_info.host_info[host_id][vid]
    port_id_list = vm_info["port_id"]
    port_no = len(port_id_list)
    ckQH = []
    for i in xrange(0,port_no):
        port_id = vm_info["port_id"][i]
        ip   = vm_info["src_ip"][i]
        mac  = vm_info["mac_addr"][i]
        dst_ip_int = vm_info["dst_ip_int"][i]
        dst_mac_int = vm_info["dst_mac_int"][i]
        net_type = vm_info["net_type"][i]

        if getpass.getuser() == "root" and net_type == "vlan":
            ckQH.append(DHCPChecker(phy_interface, port_id, mac, net_type))


    for checker in ckQH:
        checker.run()

    #ck.Checker.jLog.write_log()
