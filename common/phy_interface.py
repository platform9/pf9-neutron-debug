import subprocess


def get_phy_interface(bridge_name):
    out = subprocess.Popen(['ovs-vsctl','list-ports',bridge_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()
    stdout = stdout.decode()
    ports = stdout.split("\n")
    for port in ports:
        if "phy" not in port and len(port) > 0:
           return port
    return "No nic found"

