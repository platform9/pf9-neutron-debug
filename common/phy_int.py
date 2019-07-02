
import subprocess
import re

def ovs_output():
    with open("ovs-vsctl") as f:
        output = f.readlines()
    return output

def find_phy_line():
    output = ovs_output()
    interface = ""
    has_type = True
    for line in output:
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

def parse_line(line):
    element = line.split(" ")
    element = element[-1]
    m = re.findall("[\w\d]+",element)
    return m[0]

def get_phy_interface():
    int_line = find_phy_line()
    return parse_line(int_line)

if __name__ == "__main__":
    int_line =  find_phy_line()
    print parse_line(int_line)
