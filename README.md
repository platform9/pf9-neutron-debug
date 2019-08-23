# pf9-neutron-debug
Neutron Debugging Tool

### Objective: 
- A networking service that accepts a VM name or UUID via api curl request.
- Runs packet injection on VM and sets up packet listeners at various network interfaces. 
- Returns packet data showing broken points in network plumbing.
- Orchestrated from the DU itself: can be run over multiple hosts and service invoked from user machine.

### Tools Used:
- RabbitMQ - Oslo Messaging
- OpenStack Python SDK - Network and Port information
- Scapy and pcap - Packet injection and listening on interfaces.
- Flask Web Server - Accept api requests

### Workflow:
1. User makes a HTTP request containing VM UUID and network checker type to the service on the DU.(Network checker types and   curl format are described further down page)
2. Based on VM UUID and checker type that user passed in, the DU uses the OpenStack SDK to retrieve all relevant information about VM network, OVS bridge structure, interface names, host ID, etc. and stores this information in a JSON.
3. Uses RabbitMQ RPC Server to send this JSON to relevant hosts.
4. Hosts receive JSON and place packet listeners on interfaces mentioned in JSON.
5. Once all packet listeners are set up and waiting, DU sends another RPC call to VM host in order to inject packet at VM's qbr interface.
6. After packet injection is complete, DU sends a final RPC call to retrieve the packet data collected by listeners.
7. Once packet data is back on DU, the data is analyzed and differences between expected and actual data is stored in logs, as well as the raw data from packet inspection.
8. Returns a more generic HTTP response to original HTTP request, actual data is stored in log described in step 7.

### How to Setup and Run:
Code is found here at pf9-neutron-debug(master).

If running from scratch: do the following before the next steps:

```
git clone https://github.com/platform9/pf9-neutron-debug
./install.sh(on venv)
pip install -r requirements.txt(on venv)
```

#### Steps:

1. Assume host-service is running. If not, run python host_debug.py --config-file neutron.conf on your virtual environment in your hosts.
2. Run python du_debug.py --config-file /etc/neutron/neutron.conf on the DU to start the DU-service.
3. Now that the service is up and running on the DU/hosts, make your curl request(check below table) with VM name and checker type to run packet injection and inspection.
4. Wait for HTTP response, and then check /var/log/neutron_debug/neutron_debug.log for more details.

| Request Type | URL                                         | Description                         |
| ------------ | ------------------------------------------- | ----------------------------------- |
| GET          | neutron_debug/v1/dhcp/<vm_name>             | Runs ping checker between vms       |
| GET          | neutron_debug/v1/ping/<source_vm>/<dest_vm> | Runs DHCP checker on vm             |
| GET          | neutron_debug/v1/fip/<vm_name>              | Runs FIP(Floating IP) checker on vm |
| GET          | neutron_debug/v1/snat/<vm_name>             | Runs SNAT checker on vm             |


### Important Files

#### DU Side
- /du_debug/du_debug.py: The main driver for the DU service. Starts up the RPC server on the DU as well as the web server to process curl requests.
- /du_debug/api/wsgi_handler.py: Contains the flask routes for api curl requests to the service, which then initializes the checker process.
- /du_debug/du_rpc_handler.py: Contains the class that has every RPC method call necessary to run packet listeners, injection, and retrieval.
- /du_debug/*/*_dynamic_info.py: "*" can be either arp, dhcp, icmp, snat, or fip. These files contain discovery helper methods to get information about vm ports, vm network, layer 3, etc. for each checker type.
- /du_debug/log_data.py: Analyzes and logs packet data from hosts.

#### Host Side
- /host_debug/host_debug.py: The main driver for the Host service. Starts up the RPC server which recieves calls to run packet injection and sends data back to the DU.
- /host_debug/pcap_driver.py: Contains all pcap methods to set up listeners.
- /host_debug/scapy_driver.py: Contains all scapy methods to inject packets and pull layers off packet data.
- /host_debug/set_listeners.py: Set up pcap listeners on normal networking ports and stores in object.
- /host_debug/set_ns_listeners.py: Set up listeners on namespace ports with a manual tcpdump and stores to file.

### Notes:
- There are a few additional static checks that do not involve packet injection included in this service.
  - A heartbeat check that checks to see if VM or namespace port is down.
  - A dnsmasq checker that makes sure the DHCP process is running on each host with a DHCP server.
- This tool is currently running on Python 2.7, but is compatible with Python 3. All you must do is replace the current files with the corresponding files in the "python3" folder in pf9-neutron-debug.
