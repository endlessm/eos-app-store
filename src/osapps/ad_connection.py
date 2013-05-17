import urllib2
import os.path
import sys
import json
import socket

from eos_log import log

class AdConnection():
	ENDPOINT_SERVER = "http://localhost:3000"
	USERNAME = 'endlessos'
	PASSWORD = 'sosseldne'
	
	def __init__(self,  endpoint_config_file=os.path.expanduser("~/.endlessm/endpoint.json")):
		self._endpoint_server = self._get_endpoint_server_from_file(endpoint_config_file)
		if self._endpoint_server == None:
			self._endpoint_server = self.ENDPOINT_SERVER
			
		self._endpoint_server 

		log.info("Using endpoint " + repr(self._endpoint_server) + " for ad retrieval")

	def _get_endpoint_server_from_file(self, filename):
		endpoint = None
		try:
			with open(filename, 'r') as f:
				endpoint = str(json.load(f)['endpoint'])
		except:
			log.error("Error loading endpoint file: " + filename + " - " + repr(sys.exc_info()))

		return endpoint

	def create_request(self, path):
		self._setup_connection(self._endpoint_server, self.USERNAME, self.PASSWORD)
		return urllib2.urlopen(urllib2.Request(self._endpoint_server + path))

	def _setup_connection(self, server, username, password):
		socket.setdefaulttimeout(15)
		passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
		passman.add_password(None, server, username, password)
		authhandler = urllib2.HTTPBasicAuthHandler(passman)

		opener = urllib2.build_opener(authhandler)
		urllib2.install_opener(opener)	