#!/usr/bin/env python

import json
import time
from functools import wraps
from tacker import *
from utils import *
from em import *

# Utils (SFC Status)
from repository.utils import *

log = init_log('/home/fende/vnfm.log')

def auth(func):
    """Update authentication token and return new Tacker instance."""
    @wraps(func)
    def auth_wrapper(*args, **kwargs):
        infra = kwargs.get('infra')
        tacker = Tacker()

        try:
            response = tacker.renew_token(kwargs.get('infra'))
        except:
            return {'status': ERROR, 'error_reason': 'Infrastructure is unreachable.'}

        if not response:
            return {'status': ERROR, 'error_reason': 'Could not get authorization token.'}

        em = EMClient(infra['ip'],'9000')

        r = func(tacker=tacker, em=em, *args, **kwargs)
        return r

    return auth_wrapper

class Manager():
    """VNF Manager Implementation."""

    def __init__(self):
        self.timeout = 300  # polling timeout

    def _rollback(self, tacker, actions):
        """Rollback actions in case of errors.
        Example: actions = [['vnf', vnf_id], ['vnfd', vnfd_id]]
        """

        for action, action_id in actions:
            if action == 'vnfd':
                tacker.vnfd_delete(action_id)
                log.info('[ROLLBACK] VNFD deleted with id %s', action_id)

            elif action == 'vnf':
                tacker.vnf_delete(action_id)
                log.info('[ROLLBACK] VNF deleted with id %s', action_id)

            elif action == 'vnffgd':
                tacker.vnffgd_delete(action_id)
                log.info('[ROLLBACK] VNFFGD deleted with id %s', action_id)

    def _vnfd_create(self, tacker, vnfd):
        """Create a VNF descriptor and return its ID."""

        response = tacker.vnfd_create(vnfd)

        if response.status_code != 201:
            return (ERROR, STATUS[response.status_code])

        vnfd_id = response.json()['vnfd']['id']
        return (OK, vnfd_id)

    def _vnf_vm_create(self, tacker, vnfd_id, vnf_name):
        """Create the VM and return its ID."""

        response = tacker.vnf_create(vnfd_id, vnf_name)

        if response.status_code != 201:
            return (ERROR, STATUS[response.status_code])

        vnf_id = response.json()['vnf']['id']
        return (OK, vnf_id)

    def _get_server_id(self, tacker, vnf_id):
        """Get OpenStack server ID based on VNF ID."""

        # get VNF IP
        response = tacker.vnf_show(vnf_id)
        vnf_ip = json.loads(response.json()['vnf']['mgmt_url'])['VDU1']

        # get OpenStack servers instances
        response = tacker.get_servers()
        servers = response.json()['servers']

        # search server that has the same VNF IP
        for server in servers:
            server_mgmt_addr = server['addresses']['net_mgmt'][0]['addr']
            if server_mgmt_addr == vnf_ip:
                server_id = server['id']
                break

        return server_id

    def _get_server_private_addr(self, tacker, vnf_id):
        """Get VNF private IP."""

        # get VNF server ID
        server_id = self._get_server_id(tacker, vnf_id)

        # get all VNF addresses
        response = tacker.get_private_addr(server_id)

        if response.status_code != 200:
            error_reason = 'Could not get VNF private addr remote: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        private_addresses = response.json()['server']['addresses']['private']

        for addr in private_addresses:
            ip_version = addr['version']
            if ip_version == 4:
                private_addr = addr['addr']
                break

        return private_addr

    def _polling(self, tacker, vnf_id, user, current_sfc_name):
        """Periodically checks the status of a VNF.
        Wait until the VNF status is set to ACTIVE.
        """

        timeout = self.timeout
        sleep_interval = 2
        status_service(user, current_sfc_name, "Waiting VM to start",step=3)
        while timeout > 0:
            response = tacker.vnf_show(vnf_id)
            vnf_status = response.json()['vnf']['status']

            if vnf_status == ACTIVE:
                # TODO: what is the better way to get VNF IP? It may change
                #       depending on the VNF descriptor.
                vnf_ip = json.loads(response.json()['vnf']['mgmt_url'])['VDU1']
                return (vnf_status, vnf_ip)

            elif vnf_status == ERROR:
                error_reason = response.json()['vnf']['error_reason']
                return (vnf_status, error_reason)

            else:
                time.sleep(sleep_interval)
                timeout -= sleep_interval

        if timeout <= 0:
            error_reason = 'TIMEOUT'
            return (TIMEOUT, error_reason)

    def _vnf_polling(self, em, os_type, vnf_ip):
        """Periodically checks if VNF API is up."""

        if os_type == 'ubuntu-18.10':
            MAX_TRIES = 60
            while MAX_TRIES > 0:
                # random call to VNF API to verify if it running
                response = em.get_running(vnf_ip)

                try:
                    if response['response'].json()['running'] == 'false':
                        MAX_TRIES -= 1
                        time.sleep(1)
                    else:
                        time.sleep(5)
                        return 'OK'
                except:
                    time.sleep(1)

            return 'TIMEOUT'

        elif os_type == 'click-on-osv':
            pass

    def _vnf_init(self, em, os_type, vnf_ip, function, user, current_sfc_name):
        """Once VNF VM is fully created, initialize all tasks."""

        status_service(user, current_sfc_name, "Writing function on VNF",step=4)

        # send VNF function to VM
        log.info("Writing function to %s on %s" % (os_type, vnf_ip))
        response = em.write_function(vnf_ip, os_type, function)

        if response['status'] != 'OK':
            return (ERROR, response['error_reason'])

        status_service(user, current_sfc_name, "Installing function in VNF",step=5)

        # if VNF is Ubuntu-based, then install system packages and dependencies
        if os_type == 'ubuntu-18.10':
            log.info("Installing system packages to %s on %s" % (os_type, vnf_ip))
            response = em.install(vnf_ip)

        status_service(user, current_sfc_name, "Starting function in VNF",step=6)
        # start VNF function
        log.info("Initializing VNF %s on %s" % (os_type, vnf_ip))
        response = em.start_function(vnf_ip)

        if response['status'] != 'OK':
            return (ERROR, response['error_reason'])

        return (OK, None)

    def _static_routes(self, tacker, em, chain, action):
        """OpenStack doesn't automatically creates static route in SFC chain.
        This function adds or removes static routes between each VNF pair.
        Static routes are created in qrouter namespace.
        """

        chain = chain.split(',')

        # if SFC has a chain with just one VNF, static route isn't needed
        if len(chain) == 1:
            return

        # get VNF private address to create or delete static routes
        for i in range(len(chain[:-1])):
            vnf_src_id = chain[i]
            vnf_dst_id = chain[i+1]

            # get VNF private address
            src_addr = self._get_server_private_addr(tacker, vnf_src_id)
            dst_addr = self._get_server_private_addr(tacker, vnf_dst_id)

            em.static_route(action, dst_addr, src_addr)

    def _vnffgd_create(self, tacker, vnffgd):
        """Create VNF Forwarding Graph Descriptor."""

        response = tacker.vnffgd_create(vnffgd)

        if response.status_code != 201:
            return (ERROR, STATUS[response.status_code])

        vnffgd_id = response.json()['vnffgd']['id']
        return (OK, vnffgd_id)

    def _vnffg_create(self, tacker, vnffgd_id, vnffg_name, vnf_mapping):
        """Create VNF Forwarding Graph."""

        response = tacker.vnffg_create(vnffgd_id, vnffg_name, vnf_mapping)

        if response.status_code != 201:
            return (ERROR, STATUS[response.status_code])

        vnffg_id = response.json()['vnffg']['id']
        return (OK, vnffg_id)

    @auth
    def vnfd_delete(self, vnfd_id, infra, tacker, em):
        """Delete a VNF descriptor."""

        response = tacker.vnfd_delete(vnfd_id)

        if response.status_code != 204:
            error_reason = 'VNFD could not be deleted: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        log.info('VNFD %s successfully deleted', vnfd_id)

        return {'status': OK}

    @auth
    def vnf_function_start(self, vnf_id, vnf_ip, infra, tacker, em):
        """Start VNF function."""

        response = em.start_function(vnf_ip)

        if response['status'] != 'OK':
            error_reason = 'VNF function could not be started: %s' % response['error_reason']
            log.error(error_reason)
            return {'status': ERROR, 'error_reason': error_reason}

        log.info('VNF %s successfully started', vnf_id)

        return {'status': OK}

    @auth
    def vnf_create(self, vnfd, os_type, vnf_name, function, infra, tacker, em, user, current_sfc_name):
        """Create and initialize a VNF."""
        status_service(user, current_sfc_name, "Creating VNF",step=2)
        rollback_actions = []

        log.info('VNF is being created in the infrastructure: %s' % infra['infra_name'])

        status, data = self._vnfd_create(tacker, vnfd)

        if status == ERROR:
            error_reason = 'VNF descriptor could not be created: %s' % data
            log.error(error_reason)
            return {'status': status, 'error_reason': error_reason}

        vnfd_id = data
        log.info('VNFD created with id %s', vnfd_id)

        status, data = self._vnf_vm_create(tacker, vnfd_id, vnf_name)

        if status == ERROR:
            error_reason = 'VNF could not be created: %s' % data
            log.error(error_reason)
            rollback_actions.append(['vnfd', vnfd_id])
            self._rollback(tacker, rollback_actions)
            return {'status': status, 'error_reason': error_reason}

        vnf_id = data
        log.info('VNF is being created with id %s', vnf_id)

        # Wait until VM is fully created
        status, data = self._polling(tacker, vnf_id, user, current_sfc_name)

        if status in [ERROR, TIMEOUT]:
            error_reason = 'VNF could not be created: %s' % data
            log.error(error_reason)
            rollback_actions.append(['vnf', vnf_id])
            rollback_actions.append(['vnfd', vnfd_id])
            self._rollback(tacker, rollback_actions)
            return {'status': status, 'error_reason': error_reason}

        vnf_ip = data
        log.info('VNF %s %s is active with IP %s', os_type, vnf_id, vnf_ip)

        # Wait until all VNF dependencies are fully loaded
        # if VNF is Ubuntu-based, use VNF API to verify if VNF is up and running
        if os_type == 'ubuntu-18.10':
            # status = self._vnf_polling(em, os_type, vnf_ip)
            #
            # if status == 'TIMEOUT':
            #     error_reason = 'could not initialize VNF function: TIMEOUT'
            #     return {'status': ERROR, 'error_reason': error_reason}
            time.sleep(60)
        else:
            time.sleep(5)

        status, data = self._vnf_init(em, os_type, vnf_ip, function, user, current_sfc_name)

        if status == ERROR:
            error_reason = 'VNF function could not be initialized: %s' % data
            log.error(error_reason)
            rollback_actions.append(['vnf', vnf_id])
            rollback_actions.append(['vnfd', vnfd_id])
            self._rollback(tacker, rollback_actions)
            return {'status': status, 'error_reason': error_reason}

        log.info('VNF %s functions initialized', vnf_id)
        log.info('VNF %s successfully created', vnf_id)

        # Add VNF to be monitored
        em.manage_monitor('INSERT', vnf_id, vnf_ip)

        return {
            'status': OK,
            'vnfd_id': vnfd_id,
            'vnf_id': vnf_id,
            'vnf_ip': vnf_ip
        }

    @auth
    def vnf_resources(self, vnf_id, infra, tacker, em):
        """List VNF resources such as VDU and CPs."""

        response = tacker.vnf_resources(vnf_id)

        if response.status_code != 200:
            error_reason = 'could not get VNF resources: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        resources = response.json()['resources']

        return {
            'status': OK,
            'resources': resources
        }

    @auth
    def vnf_status(self, vnf_ip, infra, tacker, em):
        """Return VNF status."""

        response = em.get_running(vnf_ip)

        if response['status'] != 'OK':
            return {'status': ERROR, 'error_reason': response['error_reason']}

        return {'status': OK, 'vnf_status': response['response'].json()['running'].lower()}

    @auth
    def get_log(self, vnf_ip, infra, tacker, em):
        """Return VNF log."""

        response = em.get_log(vnf_ip)

        if response['status'] != 'OK':
            return {'status': ERROR, 'error_reason': response['error_reason']}

        return {'status': OK, 'log': response['response'].json()['log']}

    @auth
    def get_routers(self, infra, tacker, em):
        """Get OpenStack routers."""

        response = tacker.get_routers()
        routers = response.json()['routers']

        return {
            'status': OK,
            'routers': routers
        }

    @auth
    def get_network_src_port_id(self, infra, tacker, em):
        """Get router private port id."""

        # get OpenStack router ID
        response = tacker.get_router_id()
        router_id = response.json()['routers'][0]['id']

        # query all subnets
        response = tacker.get_subnets()
        subnets = response.json()['subnets']

        # get private subnet ID
        client_subnet_name = 'private-subnet'
        for subnet in subnets:
            if subnet['name'] == client_subnet_name:
                client_subnet_id = subnet['id']
                break

        # get router ports
        response = tacker.get_ports(router_id)
        router_ports = response.json()['ports']

        # get private subnet port ID (i.e. network_src_port_id)
        for port in router_ports:
            # Since we don't use IPv6 and each subnet has only one port in router,
            # get the first IP in the list
            if port['fixed_ips'][0]['subnet_id'] == client_subnet_id:
                network_src_port_id = port['id']
                break

        return {
            'status': OK,
            'network_src_port_id': network_src_port_id
        }

    @auth
    def get_vnc(self, vnf_id, infra, tacker, em):
        """Get VNF remote console."""

        # VNC request requires server instance ID, not VNF instance ID
        server_id = self._get_server_id(tacker, vnf_id)

        # get VNC URL
        response = tacker.get_vnc(server_id)

        if response.status_code != 200:
            error_reason = 'Could not get VNF VNC remote console: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        vnc_url = response.json()['console']['url']

        return {
            'status': OK,
            'vnc_url': vnc_url
        }

    @auth
    def create_ssh_key(self, user_name, import_key, infra, tacker, em):
        """Create or import a SSH key."""

        response = tacker.create_ssh_key(user_name, import_key)

        if response.status_code != 200:
            error_reason = 'Could not create or import SSH key: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        ssh_key = {'status': OK}

        if not import_key:
            ssh_key['private_key'] = response.json()['keypair']['private_key']

        return ssh_key

    @auth
    def delete_ssh_key(self, user_name, infra, tacker, em):
        """Delete a SSH key."""

        response = tacker.delete_ssh_key(user_name)

        if response.status_code != 202:
            error_reason = 'Could not delete SSH key: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        return {'status': OK}

    @auth
    def get_ssh_key(self, user_name, infra, tacker, em):
        """Get information about a SSH key.
        This function returns the fingerprint, public_key and creation time.
        """

        response = tacker.get_ssh_key(user_name)

        if response.status_code != 200:
            error_reason = 'Could not get SSH key: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        ssh_key = {
            'status': OK,
            'public_key': response.json()['keypair']['public_key'],
            'created_at': response.json()['keypair']['created_at'],
            'fingerprint': response.json()['keypair']['fingerprint'],
            'infra': infra['infra_name'],
            'infra_id': infra['id'],
        }

        return ssh_key

    @auth
    def sfc_create(self, vnffgd_data, vnf_mapping, infra, tacker, em, user, current_sfc_name):
        """Create a Service Function Chaining."""
        status_service(user, current_sfc_name, "Chaining VNF(s)",step=7)
        rollback_actions = []

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

        log.info('VNFFGD request: %s', vnffgd)

        # create VNFFGD
        status, data = self._vnffgd_create(tacker, json.dumps(vnffgd))

        if status == ERROR:
            error_reason = 'VNFFGD could not be created: %s' % data
            log.error(error_reason)
            return {'status': status, 'error_reason': error_reason}

        vnffgd_id = data
        log.info('VNFFGD descriptor created with id %s', vnffgd_id)

        # create VNFFG
        status, data = self._vnffg_create(tacker, vnffgd_id, vnffg_name, json.dumps(vnf_mapping))

        if status == ERROR:
            error_reason = 'VNF Forwarding Graph could not be created: %s' % data
            log.error(error_reason)
            rollback_actions.append(['vnffgd', vnffgd_id])

            for vnf_id in vnf_ids.split(','):
                rollback_actions.append(['vnf', vnf_id])

            for vnfd_id in vnfd_ids:
                rollback_actions.append(['vnfd', vnfd_id])

            self._rollback(tacker, rollback_actions)
            return {'status': status, 'error_reason': error_reason}

        vnffg_id = data
        log.info('VNFFG created with id %s', vnffg_id)

        log.info('Creating static routes on VNFFG %s', vnffg_id)
        self._static_routes(tacker, em, vnf_ids, 'create')

        log.info('VNFFG %s successfully created', vnffg_id)

        return {
            'status': OK,
            'vnffgd_id': vnffgd_id,
            'vnffg_id': vnffg_id,
            'vnffgd': vnffgd
        }

    @auth
    def sfc_delete(self, vnffg_id, vnffgd_id, vnf_ids, infra, tacker, em):
        """Delete a given VNF."""

        response = tacker.vnffg_delete(vnffg_id)

        if response.status_code != 204:
            error_reason = 'VNFFG could not be deleted: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        log.info('VNFFG %s successfully deleted', vnffg_id)

        response = tacker.vnffgd_delete(vnffgd_id)

        if response.status_code != 204:
            error_reason = 'VNFFGD could not be deleted: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        log.info('VNFFGD %s successfully deleted', vnffg_id)

        log.info('Deleting static routes on VNFFG %s' % vnffg_id)
        self._static_routes(tacker, em, vnf_ids, 'delete')

        return {'status': OK}

    @auth
    def vnf_delete(self, vnf_id, infra, tacker, em):
        """Delete a given VNF."""

        response = tacker.vnf_delete(vnf_id)

        if response.status_code != 204:
            error_reason = 'VNF could not be deleted: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        em.manage_monitor('DELETE', vnf_id, '')

        log.info('VNF %s successfully deleted', vnf_id)

        return {'status': OK}

    @auth
    def vnf_update(self, vnf_id, update_file, infra, tacker, em):
        """Update the resources of a given VNF based on a update file."""

        vnfd = """{
            "vnf": {
                "attributes": {
                    "config": {
                        "vdus": {
                            "VDU1": %s
                        }
                    }
                }
            }
        }""" % (update_file)

        vnfd = vnfd.replace("'", "\"")
        vnfd = vnfd.replace('u\"', '\"')

        response = tacker.vnf_update(vnf_id, vnfd)

        if response.status_code != 200:
            error_reason = 'VNF could not be updated: %s' % STATUS[response.status_code]
            log.error(error_reason)
            return {'status': STATUS[response.status_code], 'error_reason': error_reason}

        log.info('VNF %s successfully updated', vnf_id)

        return {'status': OK}

    @auth
    def vnf_function_update(self, vnf_id, os_type, vnf_file, infra, tacker, em):
        """Update the function of a given VNF based on a VNF file."""

        # get VNF IP and VNFD ID
        response = tacker.vnf_show(vnf_id)
        vnf_ip = json.loads(response.json()['vnf']['mgmt_url'])['VDU1']
        vnfd_id = response.json()['vnf']['vnfd_id']

        # stop the current function
        em.stop_function(vnf_ip)

        # initialize the updated function
        status, data = self._vnf_init(em, os_type, vnf_ip, vnf_file)

        if status == ERROR:
            error_reason = 'VNF function could not be updated: %s' % data
            log.error(error_reason)
            return {'status': status, 'error_reason': error_reason}

        log.info('VNF %s function successfully updated', vnf_id)

        return {'status': OK}

    @auth
    def vnf_stop(self, vnf_id, infra, tacker, em):
        """Stop the VNF function."""

        response = tacker.vnf_show(vnf_id)
        vnf_ip = json.loads(response.json()['vnf']['mgmt_url'])['VDU1']

        em.stop_function(vnf_ip)

        log.info('VNF %s function successfully stopped', vnf_id)

        return {'status': OK}

    @auth
    def vnf_restart(self, vnf_id, infra, tacker, em):
        """Restart VNF function."""

        # get VNF IP
        response = tacker.vnf_show(vnf_id)
        vnf_ip = json.loads(response.json()['vnf']['mgmt_url'])['VDU1']

        em.stop_function(vnf_ip)

        response = em.start_function(vnf_ip)

        if response['status'] != OK:
            error_reason = 'VNF function could not be restarted: %s' % response['error_reason']
            log.error(error_reason)
            return {'status': ERROR, 'error_reason': error_reason}

        log.info('VNF %s function successfully restarted', vnf_id)

        return {'status': OK}

    @auth
    def get_resource_usage(self, infra, param, tacker, em):
        """Get CPU usage from infrastructure."""

        if param == 'CPU':
            # get CPU usage
            response = em.cpu_usage(infra['ip'])

            if response['status'] != OK:
                return None
            return response['response']['cpu_usage']

        elif param == 'MEM':
            # get memory usage
            response = em.memory_usage(infra['ip'])

            if response['status'] != OK:
                return None
            return response['response']['memory_usage']

        elif param == 'BW':
            # get bandwidth usage
            response = em.bandwidth_usage(infra['ip'])

            if response['status'] != OK:
                return None
            return response['response']['bandwidth_usage']

    @auth
    def create_vpn_cert(self, infra, username, tacker, em):
        """Create OpenVPN certificates for client.
        Returns a zip file containing: ca.crt, client.crt, client.key, client.ovpn
        """

        response = em.create_vpn_cert(username)

        if response['status'] != OK:
            error_reason = 'VPN certificate could not be created.'
            log.error(error_reason)
            return {'status': ERROR, 'error_reason': error_reason}

        return {
            'status': OK,
            'certs': response['response']['certs']
        }
