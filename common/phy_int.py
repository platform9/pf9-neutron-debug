import os
import subprocess
import re

def ovs_output():
    os.system("ovs-vsctl show > ovs-vsctl.txt")
    with open("ovs-vsctl.txt") as f:
        output = f.readlines()
    os.system("rm -f ovs-vsctl.txt")
    return output

def find_phy_line(br_name):
    lines = ovs_output()
    bridge_section = False
    port_section = False
    for i in range(0, len(lines)):
        line = lines[i]
        if port_section is True:
            if "Port" in lines[i+1]:
                return line
            else:
                port_section = False
        elif bridge_section is True:
            if "Port" in line:
                port_section = True
            continue
        elif "Bridge" in line and br_name in line:
            bridge_section = True
            continue

        '''
        print line
        if "Port" in line and has_type:
            has_type = False
            continue
        elif "Port" in line:
            return interface
        if "Interface" in line:
            interface = line
        if "type" in line:
            has_type = True
        '''

def parse_line(line):
    element = re.findall('"([^"]*)"', line)
    print element
    return element[0]
    '''
    element = line.split(" ")
    element = element[-1]
    m = re.findall("[\w\d]+",element)
    return m[0]
    '''

def get_phy_interface():
    int_line = find_phy_line()
    return parse_line(int_line)

# Test function
if __name__ == "__main__":
    bridge_name = "br-vlan"
    int_line =  find_phy_line(bridge_name)
    print parse_line(int_line)
