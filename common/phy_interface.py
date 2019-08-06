import subprocess


def get_phy_interface(bridge_name):
    out = subprocess.Popen(['ovs-vsctl','list-ports',bridge_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()
    ports = stdout.split("\n")
    for port in ports:
	if "phy" not in port and len(port) > 0:
	   return port
    return "No nic found"



if __name__ == "__main__":
    bridge_name = "br-tun"
    print get_phy_interface(bridge_name) 
