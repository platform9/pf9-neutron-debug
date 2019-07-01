import os
import os_client_config
from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client

def create_client(type, cloud = None):
    if cloud is not None:
        print cloud
        client = os_client_config.make_client(
            type, cloud)
    else:
        client = os_client_config.make_client(
            type,
            auth_url=os.environ['OS_AUTH_URL'],
            username=os.environ['OS_USERNAME'],
            password=os.environ['OS_PASSWORD'],
            project_name=os.environ['OS_TENANT_NAME'])
    return client

def get_credentials():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['password'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['tenant_name'] = os.environ['OS_TENANT_NAME']
    return d

def create_client_v2(type):
    credentials = get_credentials()
    if type == "network":
        return neutron_client.Client(**credentials)
    if type == "compute":
        return nova_cient.Client(**credentials)


if __name__=="__main__":
    create_client_v2("compute")
