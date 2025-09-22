#!/usr/bin/env python

import json
import sys
import time
from utils import *
from em import *

# Wrapper Cloudstack
import uuid
import os
from cloudstack_wrapper import *


log = init_log('/root/vnfm.log')

class CloudstackManager():
    """Implementation of VNF Manager."""

    def __init__(self):
        self.timeout = 300     # polling timeout
        self.cloudstack_wrapper = CloudstackWapprer() # cloudstack interface
        self.em = EMClient('192.168.122.10','9000')   # element management interface

    def rollback(self, actions):
        """Rollback actions in case of errors.

        Example: actions = [['vnf', vnf_id], ['vnfd', vnfd_id]]
        """
        for action, action_id in actions:
            if action == 'vnfd':
                self.cloudstack_wrapper.vnfd_delete(action_id)
                log.info('[ROLLBACK] VNFD deleted with id %s', action_id)

            elif action == 'vnf':
                self.cloudstack_wrapper.vnf_delete(action_id)
                log.info('[ROLLBACK] VNF deleted with id %s', action_id)

            elif action == 'vnffgd':
                self.cloudstack_wrapper.vnffgd_delete(action_id)
                log.info('[ROLLBACK] VNFFG deleted with id %s', action_id)

    def _auth(self, infra):
        """Update authentication token and set IP of the operation."""
        response = self.cloudstack_wrapper.renew_token(infra)

        if not response:
            return {'status': ERROR, 'error_reason': 'Could not get authorization token.'}

        self.em.infra_ip = infra['ip']
        return {'status': OK}


    def _vnfd_create(self, vnfd):
        """Create a VNF descriptor and return its ID."""
        print "Creating VNFD"

        vnfd_id = uuid.uuid4()
        #vnfd_temp = open('/tmp/%s' % str(vnfd_id),'w')
        vnfd_temp = open('/home/fende/vnfds/%s' % str(vnfd_id),'w')
        vnfd_temp.write(vnfd)
        vnfd_temp.close()
        return (OK, str(vnfd_id))


    def _vnf_vm_create(self, vnfd_id, vnf_name):
        """Create the VM and return its ID."""
        status, data = self.cloudstack_wrapper.vm_create(vnfd_id, vnf_name)
        #status, data = self.cloudstack_wrapper.url_create(vnfd_id, vnf_name)
        if status == -1:
            return (ERROR,data)

        vnf_id = data
        return (OK,vnf_id)


    def _vnf_vm_stop(self, vnf_id, infra):
        """Stop the VM """
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        status, data = self.cloudstack_wrapper.vm_stop(vnf_id)
        if status == -1:
            return (ERROR,data)

        return {
            'status': OK,
            'data': data
        }

    def _vnf_vm_start(self, vnf_id, infra):
        """Start the VM """
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        status, data = self.cloudstack_wrapper.vm_start(vnf_id)
        if status == -1:
            return (ERROR,data)

        return {
            'status': OK,
            'data': data
        }

    def _vnf_vm_restart(self, vnf_id, infra):
        """Restart the VM """
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        status, data = self.cloudstack_wrapper.vm_restart(vnf_id)
        if status == -1:
            return (ERROR,data)

        status, data = self._polling(vnf_id)
        if status == 'Error':
            return {'status': ERROR, 'error_reason': data}

        return {
            'status': OK,
            'data': data
        }

    def _polling(self, vnf_id):
        """Periodically checks the status of a VNF.
        Wait until the VNF status is set to Running.
        """
        print "Waiting for VM to start"
        timeout = self.timeout
        sleep_interval = 2

        while timeout > 0:
            res = self.cloudstack_wrapper.vm_show(vnf_id)
            response = json.loads(res)

            try:
                response = response["listvirtualmachinesresponse"]["virtualmachine"][0]
                vm_status = response['state']
                print "     Status: %s" % vm_status
                if vm_status == 'Running':
                    vm_ip = response['nic'][0]['ipaddress']
                    return (vm_status, vm_ip)

                elif vm_status == 'Error':
                    error_reason = 'VM error'
                    return (vm_status, error_reason)
                else:
                    time.sleep(sleep_interval)
                    timeout -= sleep_interval

            except:
                time.sleep(sleep_interval)
                timeout -= sleep_interval

        if timeout <= 0:
            error_reason = 'TIMEOUT'
            return (TIMEOUT, error_reason)



    def _vnf_init(self, os_type, vnf_ip, function):
        """Once VNF VM is fully created, initialize all tasks."""
        print "Initializing Click Function"

        # send VNF function to VM
        response = self.em.write_function(vnf_ip, os_type, function)

        if response['status'] != 'OK':
            return (ERROR, response['error_reason'])

        # if VNF is Ubuntu-based, then install system packages and dependencies
        if os_type == 'ubuntu-18.10':
            log.info("Installing system packages to %s on %s" % (os_type, vnf_ip))
            response = self.em.install(vnf_ip)

        # start VNF function
        response = self.em.start_function(vnf_ip)

        if response['status'] != 'OK':
            return (ERROR, response['error_reason'])

        #return (OK, None)
        return response


    def _vnffgd_create(self, vnffgd):
        """Create VNF Forwarding Graph Descriptor."""
        status, data = self.cloudstack_wrapper.vnffgd_create(vnffgd)

        if status != OK:
            return (ERROR, data)

        # returns vnffgd_id
        return (OK, data)



    def _vnffg_create(self, vnffgd_id, vnffg_name, vnf_mapping):
        """Create VNF Forwarding Graph."""
        status, data = self.cloudstack_wrapper.vnffg_create(vnffgd_id, vnffg_name, vnf_mapping)

        if status != OK:
            return (ERROR, data)

        # returns vnffg_id
        return (OK, data)



    def vnfd_delete(self, vnfd_id, infra):
        """Delete a VNF descriptor."""



    def vnf_function_start(self, vnf_id, vnf_ip, infra):
        """Start VNF function."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.em.start_function(vnf_ip)

        if response['status'] != 'OK':
            return (ERROR, response['error_reason'])

        return response



    def vnf_create(self, vnfd, os_type, vnf_name, function, infra):
        """Create and initialize a VNF."""
        print "Creating VNF"
        print "INFRA: %s" % infra
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        # Creating VNFD
        status, data = self._vnfd_create(vnfd)

        if status == ERROR:
            error_reason = 'VNF descriptor could not be created: %s' % data
            log.error(error_reason)
            return {'status': status, 'error_reason': error_reason}

        vnfd_id = data

        # Creating VM
        status, data = self._vnf_vm_create(vnfd_id, vnf_name)

        if status == ERROR:
            error_reason = 'VNF could not be created: %s' % data
            #log.error(error_reason)
            #rollback_actions.append(['vnfd', vnfd_id])
            #self.rollback(rollback_actions)
            return {'status': status, 'error_reason': error_reason}

        vnf_id = data

        # Renaming VNFD with the newly created VM ID (VNF_ID)
        old_file = '/home/fende/vnfds/%s' % str(vnfd_id)
        new_file = '/home/fende/vnfds/%s' % str(vnf_id)
        os.rename(old_file,new_file)

        # Waiting for VM to be created
        status, data = self._polling(vnf_id)
        if status == 'Error':
            return {'status': ERROR, 'error_reason': data}

        vnf_ip = data

        # Prepares external access to VM and returns public IP
        vnf_ip = self.cloudstack_wrapper.prepare_net(vnf_ip, vnf_id)

        if os_type == 'ubuntu-18.10':
            time.sleep(60)
        elif os_type == 'click-on-osv':
            time.sleep(1)
        else:
            return {'status': ERROR, 'error_reason': 'Invalid OS type'}

        # Initializing function into VM
        status, data = self._vnf_init(os_type, vnf_ip, function)

        if status == ERROR:
            error_reason = 'VNF function could not be initialized: %s' % data
            return {'status': status, 'error_reason': error_reason}

        # Add VNF to be monitored
        self.em.manage_monitor('INSERT', vnf_id, vnf_ip)

        data = 'VNF %s successfully created' % vnf_id
        #return {'status': status, 'data': data}
        return {
            'status': OK,
            'vnfd_id': vnfd_id,
            'vnf_id': vnf_id,
            'vnf_ip': vnf_ip
        }


    def vnf_resources(self, vnf_id, infra):
        """List VNF resources such as VDU and CPs."""
        # O que essa funcao deve retornar?
        response = """
        {
            "resources": [
                {
                    "type": "OS::Nova::Server",
                    "name": "VDU1",
                    "id": "94c19bcf-6c89-4129-98fe-759e37e2f8c7"
                },
                {
                    "type": "OS::Neutron::Port",
                    "name": "CP21",
                    "id": "20602131-03f9-4cb2-b9fe-24bf56f1bb4f"
                },
                {
                    "type": "OS::Neutron::Port",
                    "name": "CP22",
                    "id": "ff641e7d-35f9-4095-a1f7-c3f6fb2fa294"
                },
                {
                    "type": "OS::Neutron::Port",
                    "name": "CP23",
                    "id": "ebe816df-3bc0-48a8-9278-140809d1d953"
                },
                {
                    "type": "OS::Nova::Flavor",
                    "name": "VDU1_flavor",
                    "id": "0f5e0bf2-f1a9-4474-aff9-cfffad22c5f8"
                }
            ]
        }
        """
        resources = json.loads(response)

        return {
            'status': OK,
            'resources': resources['resources']
        }

    def vnf_status(self, vnf_ip, infra):
        """Return VNF status."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.em.get_running(vnf_ip)

        if response['status'] != OK:
            return {'status': ERROR, 'error_reason': response['error_reason']}

        return {'status': OK, 'vnf_status': response['response'].json()['running']}


    def get_log(self, vnf_ip, infra):
        """Return VNF log."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.em.get_log(vnf_ip)

        if response['status'] != 'OK':
            return {'status': ERROR, 'error_reason': response['error_reason']}

        return {'status': OK, 'log': response['response'].json()['log']}


    def get_routers(self, infra):
        """Get OpenStack routers."""
        # Not implemented for Cloudstack

    def get_network_src_port_id(self, infra):
        """Get router private port id."""
        return {
            'status': OK,
            'network_src_port_id': '1'
        }

    def get_vnc(self, vnf_id, infra):
        """Get VNF remote console."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        status, data = self.cloudstack_wrapper.get_vnc(vnf_id)

        if status != OK:
            return (ERROR, data)

        return {
            'status': OK,
            'vnc_url': data
        }



    def get_ssh_key(self, user_name, infra):
        """Get information about a SSH key.
        This function returns the fingerprint, public_key and creation time.
        """
        ssh_key = {
            'status': OK,
            'public_key': 'abc',
            'created_at': 'Hoje',
            'fingerprint': 'fingerprint',
            'infra': 'UFPR (CloudStack)',
            'infra_id': '1',
        }

        return ssh_key


    def sfc_create(self, vnffgd_data, vnf_mapping, infra):
        """Create a Service Function Chaining."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        vnffgd_name = vnffgd_data['vnffgd_name']
        vnffg_name = vnffgd_data['vnffg_name']
        acl = vnffgd_data['acl']
        path = vnffgd_data['path']
        connection_point = vnffgd_data['connection_point']
        constituent_vnfs = vnffgd_data['constituent_vnfs']
        dependent_virtual_link = vnffgd_data['dependent_virtual_link']
        vnfd_ids = vnffgd_data['vnfd_ids']
        vnf_ids = vnffgd_data['vnf_ids']

        vnffgd = vnffgd_template(vnffgd_name, acl, path,
                                 connection_point, constituent_vnfs,
                                 dependent_virtual_link)

        # create VNFFGD
        status, data = self._vnffgd_create(json.dumps(vnffgd))

        if status == ERROR:
            error_reason = 'VNFFGD could not be created: %s' % data
            return {'status': status, 'error_reason': error_reason}

        vnffgd_id = data

        # create VNFFG
        status, data = self._vnffg_create(vnffgd_id, vnffg_name, json.dumps(vnf_mapping))

        if status == ERROR:
            error_reason = 'VNF Forwarding Graph could not be created: %s' % data
            return {'status': status, 'error_reason': error_reason}

        vnffg_id = data

        return {
            'status': OK,
            'vnffgd_id': vnffgd_id, #ok
            'vnffg_id': vnffg_id,
            'vnffgd': vnffgd #ok
        }

        """
        vnffgd = open('/var/www/fende/vnfm/vnffgd.json','r')
        return {
            'status': OK,
            'vnffgd_id': '1',
            'vnffg_id': '1',
            'vnffgd': vnffgd.read()
        }
        """



    def sfc_delete(self, vnffg_id, vnffgd_id, infra):
        """Delete a given VNF."""
        # Not implemented for Cloudstack



    def vnf_delete(self, vnf_id, infra):
        """Delete a given VNF."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.cloudstack_wrapper.vm_delete(vnf_id)
        if response[0] != 1:
            error_reason = 'VNF could not be deleted: %s' % response[1]
            return {'status': ERROR, 'error_reason': error_reason}

        return {'status': OK}


    def vnf_update(self, vnf_id, update_file, infra):
        """Update the resources of a given VNF based on a update file."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.cloudstack_wrapper.vm_update(vnf_id, update_file)

        return response


    def vnf_function_update(self, vnf_id, os_type, vnf_file, infra):
        """Update the function of a given VNF based on a VNFD file."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        # get VNF IP
        response = self.cloudstack_wrapper.vm_show(vnf_id)
        response = json.loads(response)
        response = response['listvirtualmachinesresponse']['virtualmachine'][0]['nic']
        for item in response:
            if item['networkname'] == 'net_mgmt':
                ip_address = item['ipaddress']

        public_ip_address = self.cloudstack_wrapper.get_public_ip_address(ip_address)

        # stop the current function
        self.em.stop_function(public_ip_address)

        # initialize the updated function
        time.sleep(1)

        status, data = self._vnf_init(os_type, public_ip_address, vnf_file)

        if status == ERROR:
            error_reason = 'VNF function could not be updated: %s' % data
            return {'status': status, 'error_reason': error_reason}

        return {'status': OK}



    def vnf_stop(self, vnf_id, infra):
        """Stop the VNF function."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.cloudstack_wrapper.vm_show(vnf_id)
        response = json.loads(response)
        response = response['listvirtualmachinesresponse']['virtualmachine'][0]['nic']
        for item in response:
            if item['networkname'] == 'net_mgmt':
                ip_address = item['ipaddress']

        public_ip_address = self.cloudstack_wrapper.get_public_ip_address(ip_address)

        self.em.stop_function(public_ip_address)

        return {'status': OK}


    def vnf_restart(self, vnf_id, infra):
        """Restart the VNF function."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        #Get public IP
        response = self.cloudstack_wrapper.vm_show(vnf_id)
        response = json.loads(response)
        response = response['listvirtualmachinesresponse']['virtualmachine'][0]['nic']
        for item in response:
            if item['networkname'] == 'net_mgmt':
                ip_address = item['ipaddress']

        public_ip_address = self.cloudstack_wrapper.get_public_ip_address(ip_address)

        # Stop
        self.em.stop_function(public_ip_address)

        time.sleep(1)

        # Start
        response = self.em.start_function(public_ip_address)
        if response['status'] != OK:
            return {'status': ERROR, 'error_reason': response['error_reason']}

        return {'status': OK}


    def get_resource_usage(self, infra, param):
        """Get CPU usage from infrastructure."""

        if param == 'CPU':
            # get CPU usage
            response = self.em.cpu_usage(infra['ip'])

            if response['status'] != OK:
                return None
            else:
                return response['response']['cpu_usage']

        elif param == 'MEM':
            # get memory usage
            response = self.em.memory_usage(infra['ip'])

            if response['status'] != OK:
                return None
            else:
                return response['response']['memory_usage']

        elif param == 'BW':
            # get bandwidth usage
            response = self.em.bandwidth_usage(infra['ip'])

            if response['status'] != OK:
                return None
            else:
                return response['response']['bandwidth_usage']
