import json
import os
import requests
import time

INFRA_ERROR_MSG = 'Infrastructure could not be reached.'

class EMClient():

    def __init__(self, infra_ip, gateway_port):
        self.infra_ip = infra_ip
        self.gateway_port = gateway_port
        self.headers = {'Content-Type': 'application/json'}
        self.timeout = 2

    def create_vpn_cert(self, username):
        url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/vpn/create'
        data = {'remote_server': self.infra_ip, 'username': username}

        try:
            response = requests.post(url, data=json.dumps(data), headers=self.headers)
            if response.json()['certs'] != None:
                return {'status': 'OK', 'response': response.json()}
            return {'status': 'ERROR', 'error_reason': 'Could not create VPN certificates.'}
        except:
            return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}

    def manage_monitor(self, action, vnf_id, vnf_ip):
        url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/em/monitor_action'
        data = {'action': action, 'vnf_id': vnf_id, 'vnf_ip': vnf_ip}
        requests.post(url, data=json.dumps(data), headers=self.headers)

    def cpu_usage(self, infra_ip):
        url = 'http://' + infra_ip + ':' + self.gateway_port + '/em/cpu_usage'

        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.json()['cpu_usage'] != None:
                return {'status': 'OK', 'response': response.json()}
            return {'status': 'ERROR', 'error_reason': 'Could not get CPU usage.'}
        except:
            return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}

    def bandwidth_usage(self, infra_ip):
        url = 'http://' + infra_ip + ':' + self.gateway_port + '/em/bandwidth_usage'

        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.json()['bandwidth_usage'] != None:
                return {'status': 'OK', 'response': response.json()}
            return {'status': 'ERROR', 'error_reason': 'Could not get bandwidth usage.'}
        except:
            return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}

    def memory_usage(self, infra_ip):
        url = 'http://' + infra_ip + ':' + self.gateway_port + '/em/memory_usage'

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.json()['memory_usage'] != None:
                return {'status': 'OK', 'response': response.json()}
            return {'status': 'ERROR', 'error_reason': 'Could not get memory usage.'}
        except:
            return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}

    def get_running(self, vnf_ip):
        url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/em/get_running'
        data = {'vnf_ip': vnf_ip}

        try:
            response = requests.get(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
            return {'status': 'OK', 'response': response}
        except:
            return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}

    def get_log(self, vnf_ip):
        url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/em/get_log'
        data = {'vnf_ip': vnf_ip}

        try:
            response = requests.get(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
            return {'status': 'OK', 'response': response}
        except:
            return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}

    def get_metrics(self, vnf_ip):
        url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/em/get_metrics'
        data = {'vnf_ip': vnf_ip}

        try:
            response = requests.get(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
            return {'status': 'OK', 'response': response}
        except:
            return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}

    def write_function(self, vnf_ip, os_type, function):
        if os_type == 'ubuntu-18.10':
            url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/em/write_function/ubuntu'
            data = {'vnf_ip': vnf_ip}
            files = {
                'json': (None, json.dumps(data), 'application/json'),
                'file': (os.path.basename(function), open(function, 'rb'), 'application/octet-stream')
            }

            response = requests.post(url, files=files)
            return {'status': 'OK', 'response': response.json()}
        else:
            url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/em/write_function'
            data = {'vnf_ip': vnf_ip, 'function': function}

            try:
                response = requests.post(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)

                # test if VNF function was inserted successfully
                if response.json()['function'] != None:
                    return {'status': 'OK', 'response': response.json()}
                return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}
            except:
                return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}

    def install(self, vnf_ip):
        url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/em/install'
        data = {'vnf_ip': vnf_ip}

        response = requests.post(url, data=json.dumps(data), headers=self.headers)
        return {'status': 'OK', 'response': response.json()}

    def start_function(self, vnf_ip):
        url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/em/start_function'
        data = {'vnf_ip': vnf_ip}

        response = requests.post(url, data=json.dumps(data), headers=self.headers)
        return {'status': 'OK', 'response': response.json()}

    def stop_function(self, vnf_ip):
        url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/em/stop_function'
        data = {'vnf_ip': vnf_ip}

        try:
            response = requests.post(url, data=json.dumps(data), headers=self.headers, timeout=self.timeout)
            return {'status': 'OK', 'response': response}
        except:
            return {'status': 'ERROR', 'error_reason': INFRA_ERROR_MSG}

    def static_route(self, action, dst_addr, src_addr):
        url = 'http://' + self.infra_ip + ':' + self.gateway_port + '/infra/static_routes'
        data = {
            'action': action,
            'dst_addr': dst_addr,
            'src_addr': src_addr
        }

        requests.post(url, data=json.dumps(data), headers=self.headers)
