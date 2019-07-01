import os_clients
import sys
from pprint import pprint

class GlobalOSInfo:
    ''' Do a query to the OpenStack SDK and store all the infomation in
        a  dictionary '''

    def __init__(self):
        cloud = None
        if len(sys.argv) > 3:
            cloud = sys.argv[3]

        self.nova = os_clients.create_client('compute', cloud = cloud)
        self.neutron = os_clients.create_client('network', cloud = cloud)

        self.os_global_info = {}
        self.os_global_info['routers_all'] = self.router_all_query()
        self.os_global_info['subnets_all'] = self.subnet_all_query()
        self.os_global_info['ports_all'] = self.port_all_query()
        self.os_global_info['networks_all'] = self.network_all_query()
        self.os_global_info['agents_all'] = self.agent_all_query()
        self.os_global_info['security_groups_all'] = self.security_groups_all_query()
        self.os_global_info['servers_all'] = self.server_all_query()
        self.os_global_info['fip_all'] = self.fip_all_query()

    def server_all_query(self):
        server_list = self.nova.servers.list(search_opts={'all_tenants': 1})
        return server_list


    def subnet_all_query(self):
        subnet_list = self.neutron.list_subnets()
        return subnet_list['subnets']

    def port_all_query(self):
        port_list = self.neutron.list_ports()
        return port_list['ports']

    #return all routers
    def router_all_query(self):
        rt_list = self.neutron.list_routers()
        return rt_list['routers']

    def network_all_query(self):
        net_list = self.neutron.list_networks()
        return net_list['networks']

    def agent_all_query(self):
        agent_list = self.neutron.list_agents()
        return agent_list['agents']

    def security_groups_all_query(self):
        security_group_list = self.neutron.list_security_groups()
        return security_group_list['security_groups']

    def fip_all_query(self):
        fips = self.neutron.list_floatingips()
        return fips['floatingips']

    def get_all_info(self):
        return self.os_global_info

    def get_os_objs(self, key):
        return self.os_global_info[key]

    def get_server_id_all(self):
        res = []
        slist = self.os_global_info["servers_all"]
        for server in slist:
            res.append(server.id)
        return res

class VMOSInfo:
    " Gather all the OpenStack information from the GlobalOSInfo "

    def __init__(self,global_os_info,host_id):
        self.global_info = global_os_info
        self.host_id = host_id
        self.os_objs = {}
        self.pack_os_objects(host_id)

    def print_dict_val(self, dic):
        for k,v in dic.items():
          print k,v

    def print_dict_list(self,l):
        for i in l:
            self.print_dict_val(i)

    #return alist of objects of neutron agents
    #TODO: filtering the agents
    def agents_query(self,host_name):
        ret = []
        agents = self.global_info.get_os_objs('agents_all')
        for agent in agents:
            if agent['host'] == host_name:
               ret.append(agent)
        return ret

    #retrieve the server object by its id
    def server_query(self, server_id):
        server_list = self.global_info.get_os_objs('servers_all')
        for server in server_list:
            if server.id == server_id:
                return server
        print "No server found"

    #retrieve the ports object by ip address
    def ports_query(self, server_ips):
        res_list = []
        ports_list = self.global_info.get_os_objs('ports_all')
        for s_ip in server_ips:
            for port in ports_list:
                fix_ips = port['fixed_ips']
                for fix_ip in fix_ips:
                    if fix_ip['ip_address'] == s_ip:
                        res_list.append(port)
        return res_list

    #return the network object that matches the port
    #TODO: examine if the network is duplicate if network is around
    def networks_query(self, ports):
        res_list = []
        net_list = self.global_info.get_os_objs('networks_all')
        for port in ports:
            for net in net_list:
                if net['id'] == port['network_id']:
                    res_list.append(net)
                    break
        return res_list

    def subnets_query(self, ports):
        res_list = []
        #id of subnet associate with ports
        subnet_id_list = []
        for port in ports:
            for ips in port['fixed_ips']:
                subnet_id_list.append(ips['subnet_id'])

        subnet_list = self.global_info.get_os_objs('subnets_all')
        for subnet in subnet_list:
            if subnet['id'] in subnet_id_list:
                res_list.append(subnet)
                break
        return res_list

    def fip_query(self, ports):
       res_list = []
       fip_list = self.global_info.get_os_objs('fip_all')
       for port in ports:
           for fip in fip_list:
               if fip['port_id'] == port['id']:
                   res_list.append(fip)
       return res_list


    def security_groups_query(self,ports):
        rec = {}
        res_list = []
        sg_list = self.global_info.get_os_objs("security_groups_all")
        for port in ports:
            for sg in sg_list:
                sg_id = sg['id']
                if sg['id'] in port['security_groups'] and sg_id not in rec:
                    res_list.append(sg)
                    rec[sg_id] = 1
        return res_list

    #return ip address from the server
    #TODO: clarify ipv4?
    def server_ip_query(self, server):
        addr_res = []

        for netname, addresses in server.addresses.items():
            for addr in addresses:
                if addr['version'] == 4:
                    addr_res.append(addr['addr'])
        return addr_res

    def get_tenant_id(self):
        return self.os_objs['server'].tenant_id

    #retrieve the OpenStack objects and store them in a dict
    def pack_os_objects(self,server_id):
        server = self.server_query(server_id)
        self.os_objs['server'] = server
        ip_addr = self.server_ip_query(server)
        ports = self.ports_query(ip_addr)
        host_name = self.get_host_name()
        self.os_objs['ports'] = ports
        self.os_objs['networks']= self.networks_query(ports)
        self.os_objs['sec_groups'] = self.security_groups_query(ports)
        self.os_objs['agents'] = self.agents_query(host_name)
        self.os_objs['fips'] = self.fip_query(ports)
        self.os_objs['subnets'] = self.subnets_query(ports)

    def get_entity_obj(self):
        return self.os_objs

    def get_host_id(self):
        server = self.os_objs['server']
        return server._info['OS-EXT-SRV-ATTR:host']

    def get_host_name(self):
        return self.os_objs['server']._info['OS-EXT-SRV-ATTR:host']

    def get_port_info(self,param_name):
        port_info = []
        ports = self.os_objs['ports']
        key = {"host_id": "binding:host_id",
                "vif_type":"binding:vif_type",
                "status":"status",
                "tentant_id": "tenant_id"}
        if param_name in key:
            param_name = key[param_name]
        for port in ports:
            port_info.append(port[param_name])
        return port_info

    def get_security_rules(self):
        info_list = []
        sec_groups = self.os_objs["sec_groups"]
        for sec_group in sec_groups:
            info_list.append(sec_group['security_group_rules'])
        return info_list

    def get_security_group_info(self,param_name):
        sec_info = []
        for sec in self.os_objs['sec_groups']:
            sec_info.append(sec[param_name])
        return sec_info

    def get_net_info(self,param_name):
        key = param_name
        if key == 'type':
            key = 'provider:network_type'
        elif key == 'seg_id':
            key = 'provider:segmentation_id'
        info_list = []
        nets = self.os_objs['networks']
        for net in nets:
           info_list.append(net[key])
        return info_list

    def get_server(self):
        return self.os_objs["server"]

    def get_agent_info(self, para_name):
        info_list = []
        for agent in self.os_objs["agents"]:
            info_list.append(agent[para_name])
        return info_list

    def get_router_info(self, para_name):
        info_list = []
        for router in self.os_objs["routers"]:
            info_list.append(router[para_name])
        return info_list

    def get_fip_info(self, para_name):
        info_list = []
        for fip in self.os_objs['fips']:
            print fip
            info_list.append(fip[para_name])
        return info_list

    def get_subnet_info(self, para_name):
        info_list = []
        for subnet in self.os_objs['subnets']:
            info_list.append(subnet[para_name])
        return info_list


class HostInfo:
    "Information send to the host agents"

    def __init__(self, global_os_info, vm_info_collection):
        self.global_os_info = global_os_info
        "dictionary with [hosts][vms][infos] as key"
        self.host_info = {}
        self.vm_info_collection = vm_info_collection
        self.get_host_dict()
        #vm ip with a given net id
        self.net_vm_ip = {}

        for vm in vm_info_collection:
            self.add_vm_info(vm_info_collection[vm])

        self.pair_vm_internal_net()
        #print self.host_info

    #Adding what hosts we have
    def get_host_dict(self):
        server_list = self.global_os_info.get_os_objs("servers_all")
        for server in server_list:
            host_id = server._info["OS-EXT-SRV-ATTR:host"]
            if host_id not in self.host_info:
                self.host_info[host_id] = {}

    def add_vm_info(self,vm_info):
        #adding vm information
        #    port number, mac address of the VM
        vm_info_to_host = {}

        vm_id = vm_info.get_server()._info['id']
        vm_info_to_host["vm_id"] = vm_id

        vm_info_to_host["port_id"] = []
        vm_info_to_host["mac_addr"] = []
        vm_info_to_host["src_ip"] = []
        vm_info_to_host["net_id"] = []
        vm_info_to_host["dst_ip_int"] = []
        vm_info_to_host["dst_mac_int"] = []

        for port in vm_info.os_objs["ports"]:
            #one-to-one mapping of port, mac, ip address and network
            vm_info_to_host["port_id"].append(port["id"])
            vm_mac = port["mac_address"]
            vm_info_to_host["mac_addr"].append(vm_mac)
            vm_ip = port["fixed_ips"][0]["ip_address"]
            vm_info_to_host["src_ip"].append(vm_ip)
            net_id = port["network_id"]
            vm_info_to_host["net_id"].append(net_id)
            if net_id not in self.net_vm_ip:
                self.net_vm_ip[net_id] = []
            self.net_vm_ip[net_id].append((vm_id, vm_ip, vm_mac))

        vm_info_to_host["net_type"] = vm_info.get_net_info("type")
        vm_id = vm_info_to_host["vm_id"]
        host_id = vm_info.get_host_id()
        self.host_info[host_id][vm_id] = vm_info_to_host

        print self.net_vm_ip

        #    ip address of external network

    #find ip and mac address of a VM in the same internal network
    #fill in None if the VM is the only VM
    def pair_vm_internal_net(self):
        for host in self.host_info:
            for vm in self.host_info[host]:
                #The net VM is on, for each net, we find a peer
                for nid in self.host_info[host][vm]["net_id"]:
                    #all the VM on that net
                    dst_mac = None
                    dst_ip = None
                    vm_peers = self.net_vm_ip[nid]
                    print vm_peers
                    for vm_p in vm_peers:
                        if vm_p[0] != vm:
                            dst_ip = vm_p[1]
                            dst_mac = vm_p[2]
                            break

                    self.host_info[host][vm]["dst_ip_int"].append(dst_ip)
                    self.host_info[host][vm]["dst_mac_int"].append(dst_mac)

    #find the dhcp agent for a given VM on a network
    def find_dhcp_agent(self):
        pass

if __name__ == "__main__":
    print "os_info.py"
    #info_gather = InfoGather("2fda064d-3df4-47fa-902a-13e66ef08f7a")
    #info_gather.fip_query("iab")
    #print info_gather.get_host_id()
    #print info_gather.get_net_info('status')
    #for i in xrange(1,10):
    #    print ""
    #info_gather.get_security_rules()
    os_info = GlobalOSInfo()
    vm_info = VMOSInfo(os_info,"9ec21ada-8527-4635-ab39-fc3aebc876f6")
