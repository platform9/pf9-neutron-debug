from neutronclient.v2_0 import client as neutron_client
from novaclient import client as nova_client
import pdb
import os
from keystoneauth1 import identity
from keystoneauth1 import session

# Creates a neutron client to access APIs
def make_neutron_object():

    neutron_session = create_credentials()
    neutron = neutron_client.Client(session=neutron_session)
    return neutron

def create_credentials():
    creds = {}
    creds['username'] = os.environ['OS_USERNAME']
    creds['password'] = os.environ['OS_PASSWORD']
    creds['auth_url'] = os.environ['OS_AUTH_URL']
    creds['tenant_name'] = os.environ['OS_TENANT_NAME']

    auth = identity.Password(auth_url=os.environ['OS_AUTH_URL'],
                         username=os.environ['OS_USERNAME'],
                         password=os.environ['OS_PASSWORD'],
                         project_name=os.environ['OS_PROJECT_NAME'],
                         project_domain_id='default',
                         user_domain_id='default')

    sess = session.Session(auth=auth)
    return sess
