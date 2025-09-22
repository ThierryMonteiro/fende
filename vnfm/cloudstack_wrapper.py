#!/usr/bin/env python

import urllib2
import urllib
import hashlib
import hmac
import base64
import json
import time
from utils import *
import os
import uuid

class CloudstackWapprer():
	"""Implementation of CloudStack's REST API interface."""
	global request
	request = {}

	def renew_token(self, infra):
		"""Renew authentication token."""
		self.infra = infra
		return "ok"

	def get_apikey(self):
		"""Return the apikey used to authenticate requests."""
		#return '-dZIGBADWFdbgfHFUfW4U0ish08o5m6IoMuFm4cVe5_Fp_ZNhLyq0OjQZ0vN--t6xXqfhn7SJ73rt5pzWr-WfQ'
		#print "api key: %s" % infra['api_key']
		return self.infra['api_key']

	def get_secretkey(self):
		"""Return the secretkey used to authenticate requests."""
		#return 'qs6biZsd7gUdOvVFcKP1VP5gUlfOm2NoLaPMOVGlyjy7adT8Ke0TD7ZjBP0NuKpKhJ-vm3uYVi8EGbftjaQoxQ'
		return self.infra['secret_key']

	def generate_url(self):
		baseurl='http://%s:8080/client/api?' % self.infra['ip']
		request_str='&'.join(['='.join([k,urllib.quote_plus(request[k])]) for k in request.keys()])

		sig_str='&'.join(['='.join([k.lower(),urllib.quote_plus(request[k].lower().replace('+','%20'))])for k in sorted(request.iterkeys())])
		sig=hmac.new(self.get_secretkey(),sig_str,hashlib.sha1)
		sig=hmac.new(self.get_secretkey(),sig_str,hashlib.sha1).digest()
		sig=base64.encodestring(hmac.new(self.get_secretkey(),sig_str,hashlib.sha1).digest())
		sig=base64.encodestring(hmac.new(self.get_secretkey(),sig_str,hashlib.sha1).digest()).strip()
		sig=urllib.quote_plus(base64.encodestring(hmac.new(self.get_secretkey(),sig_str,hashlib.sha1).digest()).strip())

		url=baseurl+request_str+'&signature='+sig

		return url

	def generate_console_url(self):
		baseurl='http://%s:8080/client/console?' % self.infra['ip']
		request_str='&'.join(['='.join([k,urllib.quote_plus(request[k])]) for k in request.keys()])

		sig_str='&'.join(['='.join([k.lower(),urllib.quote_plus(request[k].lower().replace('+','%20'))])for k in sorted(request.iterkeys())])
		sig=hmac.new(self.get_secretkey(),sig_str,hashlib.sha1)
		sig=hmac.new(self.get_secretkey(),sig_str,hashlib.sha1).digest()
		sig=base64.encodestring(hmac.new(self.get_secretkey(),sig_str,hashlib.sha1).digest())
		sig=base64.encodestring(hmac.new(self.get_secretkey(),sig_str,hashlib.sha1).digest()).strip()
		sig=urllib.quote_plus(base64.encodestring(hmac.new(self.get_secretkey(),sig_str,hashlib.sha1).digest()).strip())

		url=baseurl+request_str+'&signature='+sig

		return url

	def vm_create(self, vnfd_id, vnf_name):
		""" Create a VM """
		print "Creating a VM"
		try:
			file = '/home/fende/vnfds/%s' % str(vnfd_id)
			vnfd = open(file,'r')
		except:
			#return (ERROR, "CLOUDSTACK-WRAPPER: Couldn't open VNFD")
			return {'status':ERROR, 'error_reason':"CLOUDSTACK-WRAPPER: Could not open VNFD"}

		data = self.parse_json(vnfd.read())

		command = 'deployVirtualMachine'
		request.clear()
		request['command']=command
		request['zoneid']=self.infra['zone_id']
		request['serviceofferingid']=data['serviceoffering_id']
		request['hostid']=self.infra['host_id']
		request['templateid']='%s' % data["template_id"]
		request['displayname']='%s' % vnf_name
		request['displayvm']='true' # to show vm in dashboard
		request['size']=data['disk']

		i = 1
		for item in data['network']:
			if data['network'][item]['mgmt'] == 'true':
				a = 'iptonetworklist[0].networkid'
			else:
				a = 'iptonetworklist[%s].networkid' % i
				i+=1
			request[a]=data['network'][item]['net_id']
			
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()

		try:
			response=urllib2.urlopen(url)
		except:
			print "ERRO ao executar a url"
			return (-1, "CLOUDSTACK-WRAPPER: Could not create VM (URL error)")

		response = response.read()
		response = json.loads(response)
		vm_id = response['deployvirtualmachineresponse']['id']


		return (1, vm_id)

	def vm_stop(self, vnf_id):
		""" Stop a given VM """
		command = 'stopVirtualMachine'
		request.clear()
		request['command']=command
		request['id']=vnf_id
		request['forced']='true'
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()
		try:
			res=urllib2.urlopen(url)
		except:
			return (-1, "CLOUDSTACK-WRAPPER: Could not stoped VM (URL error)")
		response = res.read()
		response = json.loads(response)
		#print "Response Stop VM: %s" % response
		
		jobid = response['stopvirtualmachineresponse']['jobid']
		status = 0
		while status == 0:
			time.sleep(2)
			response = self.job(jobid)
			status = response['queryasyncjobresultresponse']['jobstatus']
			if status != 0 and response['queryasyncjobresultresponse']['jobresultcode'] != 0:
				return (-1, "CLOUDSTACK-WRAPPER: Could not stoped VM")

		return (1, "CLOUDSTACK-WRAPPER: VM stoped successfully")



	def vm_start(self, vnf_id):
		""" Start a given VM """
		command = 'startVirtualMachine'
		request.clear()
		request['command']=command
		request['id']=vnf_id
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()
		try:
			res=urllib2.urlopen(url)
		except:
			return (-1, "CLOUDSTACK-WRAPPER: Could not started VM (URL error)")
		response = res.read()
		response = json.loads(response)
		#print "Response Start VM: %s" % response
		
		jobid = response['startvirtualmachineresponse']['jobid']
		status = 0
		while status == 0:
			time.sleep(2)
			response = self.job(jobid)
			status = response['queryasyncjobresultresponse']['jobstatus']
			if status != 0 and response['queryasyncjobresultresponse']['jobresultcode'] != 0:
				return (-1, "CLOUDSTACK-WRAPPER: Could not start VM")

		return (1, "CLOUDSTACK-WRAPPER: VM started successfully")



	def vm_restart(self, vnf_id):
		""" Restart a given VM """
		command = 'rebootVirtualMachine'
		request.clear()
		request['command']=command
		request['id']=vnf_id
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()
		try:
			res=urllib2.urlopen(url)
		except:
			return (-1, "CLOUDSTACK-WRAPPER: Could not reboot VM (URL error)")
		response = res.read()
		response = json.loads(response)
		
		jobid = response['rebootvirtualmachineresponse']['jobid']
		status = 0
		while status == 0:
			time.sleep(2)
			response = self.job(jobid)
			status = response['queryasyncjobresultresponse']['jobstatus']
			if status != 0 and response['queryasyncjobresultresponse']['jobresultcode'] != 0:
				return (-1, "CLOUDSTACK-WRAPPER: Could not reboot VM")

		return (1, "CLOUDSTACK-WRAPPER: VM rebooted successfully")



	def vm_delete(self, vnf_id):
		""" Delete a given VM """

		# Getting IP address
		response = self.vm_show(vnf_id)
		response = json.loads(response)

		
		command = 'destroyVirtualMachine'
		request.clear()
		request['command']=command
		request['id']=vnf_id
		request['expunge']='true'
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()
		try:
			res=urllib2.urlopen(url)
		except:
			return (-1, "CLOUDSTACK-WRAPPER: Could not destroy VM (URL error)")
		response = res.read()
		response = json.loads(response)
		#print "Delete response: %s" % response
		#print "Response1: %s" % response
		
		jobid = response['destroyvirtualmachineresponse']['jobid']
		status = 0
		while status == 0:
			time.sleep(2)
			response = self.job(jobid)
			status = response['queryasyncjobresultresponse']['jobstatus']
			if status != 0 and response['queryasyncjobresultresponse']['jobresultcode'] != 0:
				return (-1, "CLOUDSTACK-WRAPPER: Could not delete VM")

		# Deleting VNFD
		file = '/home/fende/vnfds/%s' % str(vnf_id)
		os.remove(file)

		return (1, "CLOUDSTACK-WRAPPER: VM destroyed successfully")


	def vm_update(self, vnf_id, vnfd):
		""" Update a given VM """
		
		# obter as informacoes atuais da vm

		# obter as informacoes do descritor
		data = self.parse_json(vnfd)
		print "response recebida: %s" % data
		print
		print "Disco: %s" % data['disk']
		#print "service: %s" % x['serviceoffering_id']
        #print "template: %s" % x['template_id']
        #print "disk: %s" % data['disk']
		# comparar as informacoes e alterar as que estiverem diferentes

		# substituir o antigo descritor pelo novo


	def vm_show(self, vnf_id):
		command = 'listVirtualMachines'
		request.clear()
		request['command']=command
		request['id']='%s' % vnf_id
		request['response']='json'
		request['apikey']= self.get_apikey()
		
		url = self.generate_url()

		try:
			response=urllib2.urlopen(url)
			response = response.read()
		except:
			return (-1, "CLOUDSTACK-WRAPPER: Could not list VM (URL error)")
		return response



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



	def get_vnc(self, vnf_id):
		""" Get a VNC URL """
		command = 'access'
		request.clear()
		request['cmd']=command
		request['vm']=vnf_id
		request['response']='json'
		request['apikey']= self.get_apikey()
		url = self.generate_console_url()
		return (OK, url)



	def parse_json(self, data):
		data = json.loads(data)
		resources={}
		resources = data["vnfd"]["attributes"]["vnfd"]["topology_template"]["node_templates"]["VDU1"]["capabilities"]["nfv_compute"]["properties"]
		
		#Service Offering
		cpu = resources["num_cpus"]
		memory = resources["mem_size"]
		memory = memory.replace(" MB", "")
		memory = memory.replace(" GB", "000")
		serviceoffering_id = self.get_or_create_service_offering(cpu, memory)

		# Template
		template_name={}
		template_name = data["vnfd"]["attributes"]["vnfd"]["topology_template"]["node_templates"]["VDU1"]["properties"]["image"]
		template_id = self.get_template(template_name)

		# Disk (Instance)
		disk = resources["disk_size"]
		disk = disk.replace(" GB", "")
		print "Disk: %s" % disk

		# Network
		node_templates = {}
		node_templates = data["vnfd"]["attributes"]["vnfd"]["topology_template"]["node_templates"]
		net_names = []
		for item in node_templates:
			if node_templates[item]['type']  == 'tosca.nodes.nfv.VL':
				net_names.insert(0,node_templates[item]['properties']['network_name'])
		net_names = sorted(net_names)

		net_ids = self.get_network_id(net_names)
		
		network = {}
		
		for x in range(0, len(net_ids)):
			mgmt = 'false'
			if net_ids[x]['net_name'] == 'net_mgmt':
				mgmt = 'true'
			network[x]= json.loads('{"net_name":"%s", "net_id":"%s","mgmt":"%s"}' % (net_ids[x]['net_name'], net_ids[x]['net_id'], mgmt))
		print "NETWORKS: %s" % network
		response = json.loads('{"serviceoffering_id": "%s", "template_id": "%s", "disk": "%s", "network": ""}' % (serviceoffering_id,template_id,disk))
		response['network'] = network

		return response


	
	#-------------------------------------------------------------------------------
	# CloudStack Auxiliary Functions
	#-------------------------------------------------------------------------------	

	def associate_ip_address(self, networkid):
		""" Acquiring a public IP and associating with VM """
		print "Acquiring IP and associating with VM"
		command = 'associateIpAddress'
		request.clear()
		request['command']=command
		request['networkid']='%s' % networkid
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()

		try:
			res=urllib2.urlopen(url)
		except:
			print "CLOUDSTACK-WRAPPER: Cannot Acquire and Associate IP Address"
			return (-1, "CLOUDSTACK-WRAPPER: Cannot associate_ip_address")

		response = res.read()
		response = json.loads(response)

		jobid = response['associateipaddressresponse']['jobid']
		status = 0

		while status == 0:
			time.sleep(1)
			response = self.job(jobid)
			status = response['queryasyncjobresultresponse']['jobstatus']

		public_ip_id = response['queryasyncjobresultresponse']['jobresult']['ipaddress']['id']
		public_ip_address = response['queryasyncjobresultresponse']['jobresult']['ipaddress']['ipaddress']

		response = '{"public_ip_id":"%s","public_ip_address":"%s"}' % (public_ip_id, public_ip_address)

		return json.loads(response)


	def get_network_id(self, net_name):
		""" Returns network ID or multiple network IDs """
		command = 'listNetworks'
		request.clear()
		request['command']=command
		request['response']='json'
		request['apikey']= self.get_apikey()
		
		url = self.generate_url()

		try:
			response=urllib2.urlopen(url)
			response = response.read()
		except:
			return (-1, "CLOUDSTACK-WRAPPER: Error getting network IDs (URL error)")

		response = json.loads(response)
		response = response["listnetworksresponse"]["network"]

		content_type = type(net_name) 

		if content_type is str:
			for x in response:
				if x["name"]==net_name:
					return x["id"]

		elif content_type is list:
			network_ids = []
			for item in response:
				for i in net_name:
					if item["name"]==i:
						data = {'net_name':item["name"],'net_id':item["id"]}
						network_ids.append(data)
						break
			return network_ids

		else:
			return (-1, "CLOUDSTACK-WRAPPER: Error getting network IDs (invalid parameter)")
		


	def get_or_create_service_offering(self, cpu, memory):
		command = 'listServiceOfferings'
		request.clear()
		request['command']=command
		request['response']='json'
		request['apikey']= self.get_apikey()
		
		url = self.generate_url()

		res=urllib2.urlopen(url)
		response = res.read()
		response = json.loads(response)
		response = response["listserviceofferingsresponse"]
		serviceoffering_id = 'null'
		
		for item in response['serviceoffering']:
			if item['cpunumber']==int(cpu) and item['memory']==int(memory):
				serviceoffering_id = item['id']
				break

		if serviceoffering_id == 'null':
			command = 'createServiceOffering'
			request.clear()
			request['command']=command
			request['displaytext']='%scpu_%smem' % (cpu,memory)
			request['name']='%scpu_%smem' % (cpu,memory)
			request['storagetype']='shared'
			request['custom']='false'
			request['cpunumber']='%s' % cpu
			request['cpuspeed']='500'
			request['memory']='%s' % memory
			request['response']='json'
			request['apikey']= self.get_apikey()

			url = self.generate_url()
			res=urllib2.urlopen(url)

			response = res.read()
			response = json.loads(response)
			response = response['createserviceofferingresponse']['serviceoffering']
			serviceoffering_id = response['id']

		return serviceoffering_id



	def get_template(self, template_name):
		command = 'listTemplates'
		request.clear()
		request['command']=command
		request['templatefilter']='all'
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()
		res=urllib2.urlopen(url)

		response = res.read()
		response = json.loads(response)
		response = response["listtemplatesresponse"]

		template_id = 'null'

		for item in response['template']:
			if item['name']==template_name:
				template_id = item['id']
				break

		return template_id



	def job(self, job_id):
		command = 'queryAsyncJobResult'
		request['command']=command
		request['jobid']=job_id
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()

		res=urllib2.urlopen(url)
		response = res.read()

		return json.loads(response)



	def list_virtual_machines(self):
		command = 'listVirtualMachines'
		request.clear()
		request['command']=command
		#request['displayvm']='false'
		request['response']='json'
		request['apikey']= self.get_apikey()
		
		url = self.generate_url()

		res=urllib2.urlopen(url)
		print
		response = res.read()
		return json.loads(response)
		



	def prepare_net(self, vnf_private_ip, vnf_id):
		""" Prepare network to given vm """

		print "Getting network ID"
		networkid = self.get_network_id('net_mgmt')

		response = self.associate_ip_address(networkid)

		public_ip_id = response['public_ip_id']
		public_ip_address = response['public_ip_address']

		print "Enabling static NAT"
		command = 'enableStaticNat'
		request.clear()
		request['command']=command
		request['ipaddressid']='%s' % public_ip_id
		request['virtualmachineid']='%s' % vnf_id
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()
		try:
			res=urllib2.urlopen(url)
		except:
			print "CLOUDSTACK-WRAPPER: Cannot enable Static Nat"
			return (-1, "CLOUDSTACK-WRAPPER: Cannot enable Static Nat")

		response = res.read()

		print "Creating a Firewall Rule"
		command = 'createFirewallRule'
		request.clear()
		request['command']=command
		request['ipaddressid']='%s' % public_ip_id
		request['protocol']='TCP'
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()

		try:
			res=urllib2.urlopen(url)
		except:
			print "CLOUDSTACK-WRAPPER: Cannot create a firewall rule"
			return (-1, "CLOUDSTACK-WRAPPER: Cannot create a firewall rule")

		response = res.read()

		return public_ip_address



	def get_public_ip_address(self, ip_address):
		command = 'listPublicIpAddresses'
		request.clear()
		request['command']=command
		request['allocatedonly']='true'
		request['isstaticnat']='true'
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()
		try:
			res=urllib2.urlopen(url)
		except:
			print "CLOUDSTACK-WRAPPER: Cannot listPublicIpAddresses"
			#return (-1, "CLOUDSTACK-WRAPPER: Cannot release_pod_ip_address")
		response = res.read()
		response = json.loads(response)
		response = response['listpublicipaddressesresponse']['publicipaddress']

		for item in response:
			if item['vmipaddress'] == ip_address:
				public_ip_address = item['ipaddress']

		return public_ip_address



	def release_pod_ip_address(self, public_ip_id):
		command = 'releasePodIpAddress'
		request.clear()
		request['command']=command
		request['id']='%s' % public_ip_id
		request['response']='json'
		request['apikey']= self.get_apikey()

		url = self.generate_url()
		try:
			res=urllib2.urlopen(url)
		except:
			print "CLOUDSTACK-WRAPPER: Cannot release IP Address"

		response = res.read()

