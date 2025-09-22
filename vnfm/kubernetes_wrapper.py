#!/usr/bin/env python

import urllib3
import hashlib
import hmac
import base64
import json
import time
from utils import *
import os
import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import uuid

import ast

class KubernetesWrapper():
	"""Implementation of Kubernetes's API interface."""
	urllib3.disable_warnings()

	def renew_token(self, infra):
		"""Renew authentication token."""
		self.infra = infra
		return "ok"

	def get_token(self):
		return self.infra['token']

	def get_configuration(self):
		"""Returns the configuration used to authenticate requests."""
		configuration = client.Configuration()
		configuration.host="https://%s:6443" % self.infra['ip']
		configuration.verify_ssl=False
		configuration.debug = False
		configuration.api_key={"authorization":"Bearer "+ self.get_token()}
		return configuration

	def service_create(self, vnf_name, expose_port):
		print "Creating Service"
		# Creates Kubernetes Service Object
		svc = self.create_service_object(vnf_name, expose_port)
		v1 = client.CoreV1Api()
		
		try:
			response = v1.create_namespaced_service(namespace="ns-fende", body=svc)
			public_port = response.spec.ports[0].node_port
		except ApiException as e:
			return (-1, "KUBERNETES-WRAPPER: Could not create Kubernetes Service. %s" % e)
		return (1, public_port) 

	def deployment_create(self, vnfd_id, vnf_name, expose_port):
		""" Create a Deployment """
		print "Creating a Deployment"
		try:
			file = '/home/fende/vnfds/%s' % str(vnfd_id)
			vnfd = open(file,'r')
		except:
			return {'status':ERROR, 'error_reason':"KUBERNETES-WRAPPER: Could not open VNFD"}
		# Gets VNFD data
		data = self.parse_json(vnfd.read())
		
		# TODO: 
		# Disk - check if kubernetes can create container with disk (storage) limits
		#        Looks like it can not do that
		# Network - check if we can create another pods networks in kubernetes or if
		#           really we can have only one network for all pods (as it is at moment)

		client.Configuration.set_default(self.get_configuration())
		
		deployment = self.create_deployment_object(vnf_name,data['image'],data['mem'],data['cpu'],expose_port)
		v1 = client.AppsV1Api()

		try:
			response = v1.create_namespaced_deployment(body=deployment,namespace="ns-fende")
		except ApiException as e:
			return (-1, "KUBERNETES-WRAPPER: Could create Deployment. %s" % e)
		deploy_name = str(response.metadata.name)

		# returns the deployment name/id
		return (1, deploy_name)

	def deployment_delete(self,vnf_id):
		print "Deleting a Deployment"
		client.Configuration.set_default(self.get_configuration())
		v1 = client.AppsV1Api()
		try:
			response = v1.delete_namespaced_deployment(name=vnf_id,namespace="ns-fende")
		except ApiException as e:
			return (-1, "KUBERNETES-WRAPPER: Could not delete Kubernetes Deployment. %s" % e)

		v1 = client.CoreV1Api()
		try:
			response = v1.delete_namespaced_service(name=vnf_id,namespace="ns-fende")
		except ApiException as e:
			return (-1, "KUBERNETES-WRAPPER: Could not delete Kubernetes Service. %s" % e)

		return (1, "KUBERNETES-WRAPPER: Deployment destroyed successfully")

	def pod_show(self,vnf_id):
		""" Get Pod Status and IP """
		print "Get a Container"
		response = self.get_deployment(vnf_id)

		if response[0] != 1:
			return (response)

		containers_response = response[1]

		containers_response_json = self.jsonify_k8_response(containers_response)

		container_name = "NULL"
		for item in containers_response_json:
			# TODO: resolver a questao do nome do container
			if item['name'] == vnf_id:
				container_name = containers_response_json[0]['name']

		if container_name == "NULL":
			return (-1, "KUBERNETES-WRAPPER: Could not find the container.")

		all_pods = self.get_pods()
		if all_pods[0] != 1:
			return (-1, "KUBERNETES-WRAPPER: Could not get pods list.")

		all_pods = all_pods[1]
		status = "NULL"
		vnf_ip = "NULL"
		for pod in all_pods:
			if pod.spec.containers[0].name == vnf_id:
				status = pod.status.phase
				vnf_ip = pod.status.pod_ip

		if status == "NULL":
			return (-1, "KUBERNETES-WRAPPER: Could not get VNF (Pod) Status.")

		if vnf_ip == "NULL":
			return (-1, "KUBERNETES-WRAPPER: Could not get VNF (Pod) IP.")

		response_data = {"status":status,"ip":vnf_ip}
		return response_data

	def pod_stop(self,vnf_id):
		return (1, "KUBERNETES-WRAPPER: Pod stoped successfully")

	def pod_start(self,vnf_id):
		return (1, "KUBERNETES-WRAPPER: Pod started successfully")

	def pod_restart(self,vnf_id):
		return (1, "KUBERNETES-WRAPPER: Pod rebooted successfully")

	def deployment_update(self,vnf_ip,update_file):
		pass

	def vnffgd_create(self, vnffgd):
		"""Create a VNF Forwarding Graph Descriptor."""
  		print "Creating VNFFGD"
		vnffgd_id = uuid.uuid4()
		vnffgd_temp = open(str(vnffgd_id),'w')
		try:
			vnffgd_temp.write(vnffgd)
		except Exception as e:
			vnffgd_temp.close()
			return (ERROR, str(e))
		vnffgd_temp.close()
		return (OK, str(vnffgd_id))


	def vnffg_create(self, vnffgd_id, name, vnf_mapping):
		# returns only a simple id
		return (OK, str(uuid.uuid4()))


	def parse_json(self, data):
		data = json.loads(data)
		resources={}
		resources = data["vnfd"]["attributes"]["vnfd"]["topology_template"]["node_templates"]["VDU1"]["capabilities"]["nfv_compute"]["properties"]
		
		# Service Offering
		cpu = resources["num_cpus"]
		memory = resources["mem_size"]
		memory = memory.replace(" MB", "Mi")
		memory = memory.replace(" GB", "Gi")

		# Template
		template_name={}
		template_name = data["vnfd"]["attributes"]["vnfd"]["topology_template"]["node_templates"]["VDU1"]["properties"]["image"]

		# Disk (Instance)
		disk = resources["disk_size"]
		disk = disk.replace(" GB", "")

		# Network
		node_templates = {}
		node_templates = data["vnfd"]["attributes"]["vnfd"]["topology_template"]["node_templates"]
		net_names = []
		for item in node_templates:
			if node_templates[item]['type']  == 'tosca.nodes.nfv.VL':
				net_names.insert(0,str(node_templates[item]['properties']['network_name']))
		net_names = json.dumps(net_names)
		
		response = json.loads('{"cpu": "%s", "mem": "%s", "disk": "%s","image":"%s","networks":%s}' % (cpu,memory,disk,template_name,net_names))

		return response

	#-------------------------------------------------------------------------------
	# Kubernetes Auxiliary Functions
	#-------------------------------------------------------------------------------	
	def create_deployment_object(self,vnf_name,image,mem,cpu,expose_port):
		# Configurate Pod template container
		print "(Deploy) Expose port: %s" % expose_port
		image_name="joseflauzino/%s:latest" % image
		container = client.V1Container(
			name=vnf_name,
			image=image_name,
			ports=[client.V1ContainerPort(container_port=int(expose_port))],
			resources={'requests':{'memory':mem,'cpu':cpu},'limits':{'memory':mem,'cpu':cpu}},
			args=['--vm', '1', '--vm-bytes', mem, '--vm-hang', '1'])
		# Create and configurate a spec section
		template = client.V1PodTemplateSpec(
			metadata=client.V1ObjectMeta(labels={'app': vnf_name,'run':vnf_name}),
			spec=client.V1PodSpec(containers=[container]))
		# Create the specification of deployment
		spec = client.V1DeploymentSpec(
			replicas=1,
			template=template,
			selector={'matchLabels': {'app': vnf_name, 'run':vnf_name}})
		# Instantiate the deployment object
		deployment = client.V1Deployment(
			api_version="apps/v1",
			kind="Deployment",
			metadata=client.V1ObjectMeta(name=vnf_name),
			spec=spec)

		return deployment

	def create_service_object(self,unique_name,expose_port):
		return json.loads("""{
				"kind": "Service",
				"apiVersion": "v1",
				"metadata": {
					"name": "%s",
					"labels": {
						"run": "%s"
					}
				},
				"spec": {
					"ports": [
						{
							"protocol": "TCP",
							"port": %s
						}
					],
					"selector": {
						"run": "%s"
					},
					"type": "NodePort"
				}
			}""" % (unique_name,unique_name,expose_port,unique_name))

		"""
		# Create the metadata of service
		metadata = client.V1ObjectMeta(
			name=unique_name,
			namespace='ns-fende',
			labels={'run': unique_name})

		# Create the specification of service
		spec = client.V1ServiceSpec(
			ports=[{'protocol': 'TCP', 'port': 80}],
			selector={'run': unique_name},
			type='NodePort')

		# Instantiate the service object
		svc = client.V1Service(
			api_version='apps/v1',
			kind='Service',
			metadata=metadata,
			spec=spec)
		print "Object: %s" % svc
		return svc
		"""

	def get_deployment(self,vnf_id):
		client.Configuration.set_default(self.get_configuration())
		v1 = client.AppsV1Api()
		try:
			response = v1.read_namespaced_deployment(name=vnf_id,namespace="ns-fende")
		except:
			return (-1, "KUBERNETES-WRAPPER: Could not get Kubernetes Deployments.")
		return (1, str(response.spec.template.spec.containers))


	def get_pods(self):
		client.Configuration.set_default(self.get_configuration())
		v1 = client.CoreV1Api()
		try:
			response = v1.list_namespaced_pod("ns-fende")
			#print "RES= %s" % str(response.status)
			#print "Tipo da resposta= %s" % type(response)
			return (1, response.items)
		except ApiException as e:
			return (-1, "KUBERNETES-WRAPPER: Could not get Kubernetes Pods. %s" % e)

	def jsonify_k8_response(self,data):
		res = ast.literal_eval(data)
		json_res = json.dumps(res)
		json_res = json.loads(json_res)
		return json_res