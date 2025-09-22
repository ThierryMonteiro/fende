#!/usr/bin/env python

import ConfigParser
import os
import requests
import json

class IdentityManager():
    """Identification and authentication of REST requests."""

    def __init__(self):
        self.timeout = 2
        self.header = {
            'Content-type' : 'application/json',
            'Accept'       : 'application/json'
        }

    def get_identity_info(self, infra):
        """Request for tokens and endpoints info."""

        tenant_name = infra['tenant_name']
        username = infra['username']
        password = infra['password']
        url = 'http://%s/' % (infra['ip'])

        data = """{
            "auth": {
                "identity": {
                    "methods": [
                        "password"
                    ],
                    "password": {
                        "user": {
                            "domain": {
                                "name": "Default"
                            },
                            "name": "%s",
                            "password": "%s"
                        }
                    }
                },
                "scope": {
                    "project": {
                        "domain": {
                            "name": "Default"
                        },
                        "name": "%s"
                    }
                }
            }
        }""" % (username, password, tenant_name)

        url += 'identity/v3/auth/tokens'

        try:
            identity = requests.post(url, data=data, headers=self.header, timeout=self.timeout)
            return identity
        except:
            return None

    def get_endpoints(self, token):
        """Get endpoints public URLs of each OpenStack service.
        These endpoints are used for future requests.
        """

        endpoints = {}
        service_catalog = token.json()['token']['catalog']

        for service in service_catalog:
            name = service['name']
            public_url = service['endpoints'][0]['url']
            endpoints[name] = public_url

        return endpoints

class Tacker():
    """Implementation of Tacker's REST API interface."""

    def __init__(self):
        self.identity = IdentityManager() # identity service

        self.header = {
            'Content-type' : 'application/json',
            'Accept'       : 'application/json',
            'X-Auth-Token' : None
        }

    def renew_token(self, infra):
        """Renew authentication token."""

        # request updated token
        identity = self.identity.get_identity_info(infra)

        if not identity:
            return None

        # set authentication token
        self.header['X-Auth-Token'] = identity.headers['X-Subject-Token']

        # update Tacker endpoint
        endpoints = self.identity.get_endpoints(identity)
        try:
            self.tacker_endpoint = endpoints['tacker']
            self.network_endpoint = endpoints['neutron']
            self.nova_endpoint = endpoints['nova']
        except:
            return None

        return "ok"

    def vnfd_show(self, vnfd_id):
        """Show details of a VNF descriptor."""

        url = self.tacker_endpoint + 'v1.0/vnfds/' + vnfd_id
        return requests.get(url, headers=self.header)

    def vnfd_create(self, vnfd):
        """Create a VNF descriptor.
        Template should be a JSON text.
        """

        url = self.tacker_endpoint + 'v1.0/vnfds'
        return requests.post(url, headers=self.header, data=vnfd)

    def vnfd_delete(self, vnfd_id):
        """Delete a given VNF descriptor."""

        url = self.tacker_endpoint + 'v1.0/vnfds/' + vnfd_id
        return requests.delete(url, headers=self.header)

    def vnfd_list(self):
        """List all available VNF descriptors."""

        url = self.tacker_endpoint + 'v1.0/vnfds'
        return requests.get(url, headers=self.header)

    def vnf_create(self, vnfd_id, vnf_name):
        """Create a instance of a VNF."""

        url = self.tacker_endpoint + 'v1.0/vnfs'
        data = """{
            "vnf": {
                "attributes": {},
                "vim_id": "",
                "description": "",
                "vnfd_id": "%s",
                "name": "%s"
            }
        }""" % (vnfd_id, vnf_name)

        return requests.post(url, headers=self.header, data=data)

    def vnf_delete(self, vnf_id):
        """Delete a given VNF."""

        url = self.tacker_endpoint + 'v1.0/vnfs/' + vnf_id
        return requests.delete(url, headers=self.header)

    def vnf_update(self, vnf_id, update_file):
        """Update a given VNF."""

        url = self.tacker_endpoint + 'v1.0/vnfs/' + vnf_id
        return requests.put(url, headers=self.header, data=update_file)

    def vnf_list(self):
        """List all VNFs."""

        url = self.tacker_endpoint + 'v1.0/vnfs'
        return requests.get(url, headers=self.header)

    def vnf_show(self, vnf_id):
        """Show info about a given VNF."""

        url = self.tacker_endpoint + 'v1.0/vnfs/' + vnf_id
        return requests.get(url, headers=self.header)

    def vnf_resources(self, vnf_id):
        """Show VDU and CP of a given VNF."""

        url = self.tacker_endpoint + 'v1.0/vnfs/%s/resources' % vnf_id
        return requests.get(url, headers=self.header)

    def get_routers(self):
        """Get all routers from OpenStack infrastructure."""

        url = self.network_endpoint + 'v2.0/routers'
        return requests.get(url, headers=self.header)

    def get_router_id(self):
        """Get router ID. The VNFM assumes that there is only one router (i.e. router1)."""

        url = self.network_endpoint + 'v2.0/routers'
        return requests.get(url, headers=self.header)

    def get_ports(self, device):
        """Query all device ports."""

        url = self.network_endpoint + 'v2.0/ports?device_id=%s' % device
        return requests.get(url, headers=self.header)

    def get_subnets(self):
        """Query all OpenStack subnets."""

        url = self.network_endpoint + 'v2.0/subnets'
        return requests.get(url, headers=self.header)

    def vnffgd_create(self, vnffgd):
        """Create a VNF Forwarding Graph Descriptor."""

        url = self.tacker_endpoint + 'v1.0/vnffgds'
        return requests.post(url, headers=self.header, data=vnffgd)

    def vnffgd_delete(self, vnffgd_id):
        """Delete a VNFFGD."""

        url = self.tacker_endpoint + 'v1.0/vnffgds/' + vnffgd_id
        return requests.delete(url, headers=self.header)

    def vnffg_create(self, vnffgd_id, name, vnf_mapping):
        """Create a VNF Forwarding Graph."""

        url = self.tacker_endpoint + 'v1.0/vnffgs'
        vnffg = """{
            "vnffg": {
                "vnffgd_id": "%s",
                "name": "%s",
                "vnf_mapping": %s,
                "symmetrical": false
            }
        }""" % (vnffgd_id, name, vnf_mapping)

        return requests.post(url, headers=self.header, data=vnffg)

    def vnffg_delete(self, vnffg_id):
        """Delete a VNF Forwarding Graph."""

        url = self.tacker_endpoint + 'v1.0/vnffgs/' + vnffg_id
        return requests.delete(url, headers=self.header)

    def get_servers(self):
        """Get all server instances from OpenStack.
        Note that server instances are different from VNF instances.
        """

        url = self.nova_endpoint + '/servers/detail'
        return requests.get(url, headers=self.header)

    def get_private_addr(self, server_id):
        """Get server IP on private subnet."""

        url = self.nova_endpoint + '/servers/%s' % server_id
        return requests.get(url, headers=self.header)

    def get_vnc(self, server_id):
        """Create a remote console through VNC."""

        url = self.nova_endpoint + '/servers/%s/action' % server_id
        action = """{
            "os-getVNCConsole": {
                "type": "novnc"
            }
        }"""

        return requests.post(url, headers=self.header, data=action)

    def create_ssh_key(self, user_name, import_key):
        """Create or import a SSH key into OpenStack server.
        If import_key is empty, a new key will be generated.
        """

        url = self.nova_endpoint + '/os-keypairs'
        data = {
            'keypair': {
                'name': user_name
            }
        }

        if import_key:
            data['keypair']['public_key'] = import_key

        data = json.dumps(data)

        return requests.post(url, headers=self.header, data=data)

    def delete_ssh_key(self, user_name):
        """Delete a SSH key from OpenStack."""

        url = self.nova_endpoint + '/os-keypairs/%s' % user_name
        return requests.delete(url, headers=self.header)

    def get_ssh_key(self, user_name):
        """Get SSH key info from OpenStack."""

        url = self.nova_endpoint + '/os-keypairs/%s' % user_name
        return requests.get(url, headers=self.header)
