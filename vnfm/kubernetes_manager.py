#!/usr/bin/env python

import json
import sys
import time
from utils import *
from em import *

# Wrapper Kubernetes
import uuid
import os
from kubernetes_wrapper import *

#Models
from repository.models.chains import *

# Utils (SFC Status)
from repository.utils import *

log = init_log('/root/vnfm.log')

class KubernetesManager():
    """Implementation of VNF Manager."""

    def __init__(self):
        self.timeout = 300     # polling timeout
        self.kubernetes_wrapper = KubernetesWrapper() # kubernetes interface
        self.em = EMClient('192.168.122.2','9000')   # element management interface

    def rollback(self, actions):
        """Rollback actions in case of errors.

        Example: actions = [['vnf', vnf_id], ['vnfd', vnfd_id]]
        """
        for action, action_id in actions:
            if action == 'vnfd':
                self.kubernetes_wrapper.vnfd_delete(action_id)
                log.info('[ROLLBACK] VNFD deleted with id %s', action_id)

            elif action == 'vnf':
                self.kubernetes_wrapper.vnf_delete(action_id)
                log.info('[ROLLBACK] VNF deleted with id %s', action_id)

            elif action == 'vnffgd':
                self.kubernetes_wrapper.vnffgd_delete(action_id)
                log.info('[ROLLBACK] VNFFG deleted with id %s', action_id)

    def _auth(self, infra):
        """Update authentication token and set IP of the operation."""
        response = self.kubernetes_wrapper.renew_token(infra)

        if not response:
            return {'status': ERROR, 'error_reason': 'Could not get authorization token.'}

        self.em.infra_ip = infra['ip']
        self.em.gateway_port = infra['gateway_port']
        return {'status': OK}


    def _vnfd_create(self, vnfd):
        """Create a VNF descriptor and return its ID."""
        print "Creating VNFD"
        vnfd_id = uuid.uuid4()
        vnfd_temp = open('/home/fende/vnfds/%s' % str(vnfd_id),'w')
        vnfd_temp.write(vnfd)
        vnfd_temp.close()
        return (OK, str(vnfd_id))


    def _vnf_deployment_create(self, vnfd_id, vnf_name, expose_port):
        """Create the Deployment and return its ID."""
        status, data = self.kubernetes_wrapper.deployment_create(vnfd_id, vnf_name,expose_port)
        if status == -1:
            return (ERROR,data)

        vnf_id = data
        return (OK,vnf_id)


    def _vnf_pod_stop(self, vnf_id, infra):
        """Stop all containers into Pod """
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        status, data = self.kubernetes_wrapper.vm_stop(vnf_id)
        if status == -1:
            return (ERROR,data)

        return {
            'status': OK,
            'data': data
        }

    def _vnf_pod_start(self, vnf_id, infra):
        """Start all containers into Pod """
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        status, data = self.kubernetes_wrapper.vm_start(vnf_id)
        if status == -1:
            return (ERROR,data)

        return {
            'status': OK,
            'data': data
        }

    def _vnf_pod_restart(self, vnf_id, infra, user, current_sfc_name):
        """Restart the all containers into Pod """
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        status, data = self.kubernetes_wrapper.pod_restart(vnf_id)
        if status == -1:
            return (ERROR,data)

        status, data = self._polling(vnf_id, user, current_sfc_name)
        if status == 'Error':
            return {'status': ERROR, 'error_reason': data}

        return {
            'status': OK,
            'data': data
        }

    def _polling(self, vnf_id, user, current_sfc_name):
        """Periodically checks the status of a VNF.
        Wait until the VNF status is set to Running.
        """
        timeout = self.timeout
        sleep_interval = 2

        # Loading: Step 3
        """
        current_sfc = SFCStatus.objects.get(current_sfc_name=current_sfc_name)
        current_sfc.status = "Waiting container to start"
        current_sfc.step = str(int(current_sfc.step) + 1)
        current_sfc.save()
        """
        status_service(user, current_sfc_name, "Waiting container to start",step=3)

        while timeout > 0:
            response = self.kubernetes_wrapper.pod_show(vnf_id)

            try:
                vm_status = response['status']

                # Loading: Step 3 (to update only vm_status)
                """
                current_sfc = SFCStatus.objects.get(current_sfc_name=current_sfc_name)
                current_sfc.status = "Waiting container to start: %s" % vm_status
                current_sfc.step = current_sfc.step # keep the same step
                current_sfc.save()
                """

                if vm_status == 'Running':
                    vm_ip = response['ip']
                    return (vm_status, vm_ip)

                elif vm_status == 'Error':
                    error_reason = 'Container error'
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



    def _vnf_init(self, os_type, vnf_ip, function, user, current_sfc_name):
        """Once VNF VM is fully created, initialize all tasks."""

        # Loading: Step 4
        """
        current_sfc = SFCStatus.objects.get(current_sfc_name=current_sfc_name)
        current_sfc.status = "Sending function to VNF"
        current_sfc.step = str(int(current_sfc.step) + 1)
        current_sfc.save()
        """
        status_service(user, current_sfc_name, "Sending function to VNF",step=4)

        # send VNF function to Container
        response = self.em.write_function(vnf_ip, os_type, function)

        if response['status'] != 'OK':
            return (ERROR, response['error_reason'])

        log.info("Installing system packages to %s on %s" % (os_type, vnf_ip))

        # Loading: Step 5
        """
        current_sfc = SFCStatus.objects.get(current_sfc_name=current_sfc_name)
        current_sfc.status = "Installing function in VNF"
        current_sfc.step = str(int(current_sfc.step) + 1)
        current_sfc.save()
        """
        status_service(user, current_sfc_name, "Installing function in VNF",step=5)
        response = self.em.install(vnf_ip)

        # Loading: Step 6
        """
        current_sfc = SFCStatus.objects.get(current_sfc_name=current_sfc_name)
        current_sfc.status = "Starting function in VNF"
        current_sfc.step = str(int(current_sfc.step) + 1)
        current_sfc.save()
        """
        status_service(user, current_sfc_name, "Starting function in VNF",step=6)

        # start VNF function
        response = self.em.start_function(vnf_ip)

        if response['status'] != 'OK':
            return (ERROR, response['error_reason'])

        return response


    def _vnffgd_create(self, vnffgd):
        """Create VNF Forwarding Graph Descriptor."""
        status, data = self.kubernetes_wrapper.vnffgd_create(vnffgd)

        if status != OK:
            return (ERROR, data)

        # returns vnffgd_id
        return (OK, data)



    def _vnffg_create(self, vnffgd_id, vnffg_name, vnf_mapping):
        """Create VNF Forwarding Graph."""
        status, data = self.kubernetes_wrapper.vnffg_create(vnffgd_id, vnffg_name, vnf_mapping)

        if status != OK:
            return (ERROR, data)

        # returns vnffg_id
        return (OK, data)



    def vnfd_delete(self, vnfd_id, infra):
        """Delete a VNF descriptor."""
        pass



    def vnf_function_start(self, vnf_id, vnf_ip, infra):
        """Start VNF function."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.em.start_function(vnf_ip)

        if response['status'] != 'OK':
            return (ERROR, response['error_reason'])

        return response



    def vnf_create(self, vnfd, os_type, vnf_name, function, infra, expose_port, user, current_sfc_name):
        """Create and initialize a VNF."""

        # Loading: Step 2
        """
        current_sfc = SFCStatus.objects.get(id=current_sfc_name)
        current_sfc.status = "Creating VNF"
        current_sfc.step = str(int(current_sfc.step) + 1)
        current_sfc.save()
        """
        status_service(user, current_sfc_name, "Creating VNF",step=2)

        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        # Creating VNFD
        status, data = self._vnfd_create(vnfd)

        if status == ERROR:
            error_reason = 'VNF descriptor could not be created: %s' % data
            status_service(user, current_sfc_name, "Could not create VNFD",error=True)
            log.error(error_reason)
            return {'status': status, 'error_reason': error_reason}

        vnfd_id = data

        # Creating Deployment
        status, data = self._vnf_deployment_create(vnfd_id, vnf_name, expose_port)

        if status == ERROR:
            status_service(user, current_sfc_name, "Could not create VNF",error=True)
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

        # Waiting for Container to be created
        status, data = self._polling(vnf_id, user, current_sfc_name)
        if status == 'Error':
            return {'status': ERROR, 'error_reason': data}

        vnf_ip = data

        time.sleep(10)

        # Initializing function into Container
        status, data = self._vnf_init(os_type, vnf_ip, function, user, current_sfc_name)

        if status == ERROR:
            error_reason = 'VNF function could not be initialized: %s' % data
            return {'status': status, 'error_reason': error_reason}

        # Add VNF to be monitored
        self.em.manage_monitor('INSERT', vnf_id, vnf_ip)

        data = 'VNF %s successfully created' % vnf_id

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
        # Not implemented for Kubernetes
        pass

    def get_network_src_port_id(self, infra):
        """Get router private port id."""
        return {
            'status': OK,
            'network_src_port_id': '1'
        }

    def get_vnc(self, vnf_id, infra):
        """Get VNF remote console."""
        pass



    def get_ssh_key(self, user_name, infra):
        """Get information about a SSH key.
        This function returns the fingerprint, public_key and creation time.
        """
        ssh_key = {
            'status': OK,
            'public_key': 'abc',
            'created_at': 'Hoje',
            'fingerprint': 'fingerprint',
            'infra': 'UFPR (Kubernetes)',
            'infra_id': '1',
        }

        return ssh_key


    def sfc_create(self, name, vnffgd_data, vnf_mapping, infra, user, current_sfc_name):
        """Create a Service Function Chaining."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        # Loading: Step 7
        """
        current_sfc = SFCStatus.objects.get(id=current_sfc_name)
        current_sfc.status = "Chaining VNF(s)"
        current_sfc.step = str(int(current_sfc.step) + 1)
        current_sfc.save()
        """
        status_service(user, current_sfc_name, "Chaining VNF(s)",step=7)

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
        
        # Create Kubernetes Service
        # print "ACL: %s" % acl
        # expose_port = acl['source_port_range']

        expose_port = vnffgd_data['expose_port']

        print "(Service) Expose Port: %s" % expose_port
        status, data = self.kubernetes_wrapper.service_create(name,expose_port)
        if status != 1:
            error_reason = 'Could not create service: %s' % data
            return {'status': ERROR, 'error_reason': error_reason}

        # Kubernetes NodePort
        public_port = data

        
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
            'vnffgd_id': vnffgd_id,
            'vnffg_id': vnffg_id,
            'vnffgd': vnffgd,
            'public_port': public_port
        }



    def sfc_delete(self, vnffg_id, vnffgd_id, infra):
        """Delete a given VNF."""
        # Not implemented for Kubernetes



    def vnf_delete(self, vnf_id, infra):
        """Delete a given VNF."""
        print "Deleting a VNF"
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.kubernetes_wrapper.deployment_delete(vnf_id)
        if response[0] != 1:
            error_reason = 'VNF could not be deleted: %s' % response[1]
            return {'status': ERROR, 'error_reason': error_reason}

        return {'status': OK}


    def vnf_update(self, vnf_id, update_file, infra):
        """Update the resources of a given VNF based on a update file."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.kubernetes_wrapper.deployment_update(vnf_id, update_file)

        return response


    def vnf_function_update(self, vnf_id, os_type, vnf_file, infra):
        """Update the function of a given VNF based on a VNFD file."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        # get VNF IP
        response = self.kubernetes_wrapper.pod_show(vnf_id)
        ip_address = response['ip']

        # stop the current function
        self.em.stop_function(ip_address)

        # initialize the updated function
        time.sleep(1)

        status, data = self._vnf_init(os_type, ip_address, vnf_file)

        if status == ERROR:
            error_reason = 'VNF function could not be updated: %s' % data
            return {'status': status, 'error_reason': error_reason}

        return {'status': OK}



    def vnf_stop(self, vnf_id, infra):
        """Stop the VNF function."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        response = self.kubernetes_wrapper.pod_show(vnf_id)
        ip_address = response['ip']

        self.em.stop_function(ip_address)

        return {'status': OK}


    def vnf_restart(self, vnf_id, infra):
        """Restart the VNF function."""
        auth = self._auth(infra)
        if auth['status'] == ERROR:
            return {'status': ERROR, 'error_reason': auth['error_reason']}

        #Get public IP
        response = self.kubernetes_wrapper.pod_show(vnf_id)
        ip_address = response['ip']

        # Stop
        self.em.stop_function(ip_address)

        time.sleep(1)

        # Start
        response = self.em.start_function(ip_address)
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