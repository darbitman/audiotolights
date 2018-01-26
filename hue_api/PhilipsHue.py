import sys
import requests as r
import time
import os

class Bridge:
	CONFIG_FILE = str()
	bridge_ip = None
	bridge_username = None
	lights = dict()
	groups = dict()
	lightlist = dict()

	def __init__(self, cfg_file_, timeout = 15):
		"""	Initialize Hue object.
		
			If cfg file exists, verify IP/name in file and if not valid, acquire new ones.
			Else, acquire new IP/name and write them to a config file.
		"""
		self.CONFIG_FILE = cfg_file_
		if os.path.exists(self.CONFIG_FILE):
			try:
				f = open(self.CONFIG_FILE, "r")
				data = f.read()
				data = data.split("\n")		# data[0] = IP, data[1] = username
			except IOError:
				print("config file doesn't exist")
			finally:
				f.close()

			if self.validate_ip(data[0]):
					self.bridge_ip = data[0]
			else:
				self.get_bridge_ip()

			if self.validate_username(data[1]):
				self.bridge_username = data[1]
			else:
				self.get_username()
		else:
			self.get_username()
			self.get_bridge_ip()
			try:
				f = open(self.CONFIG_FILE, "w")
				f.write("{}\n".format(self.bridge_ip))
				f.write("{}\n".format(self.bridge_username))
			except IOError:
				print("Error writing config file")
			finally:
				f.close();
		self.timeout = timeout
		self.initialize_lights()

	def get_bridge_ip(self):
		print("Getting bridge IP")
		"""Use Philips broker server discover process to find Philips Hue on LAN"""
		addr = "https://www.meethue.com/api/nupnp"
		response = self.get_response(addr);
		if response.raise_for_status() is None:
			response = response.json()[0]
		else:
			sys.exit("Cannot find Bridge IP Address")
		self.bridge_ip = response["internalipaddress"]
		print("Found Philips Hue at {}".format(self.bridge_ip))

	def get_response(self, addr):
		print("Getting response")
		"""Get Philips Hue status"""
		try:
			response = r.get(addr)
		except r.ConnectionError:
			sys.exit("No response received from Philips Hue. Ensure that it is powered and connected to the network.")
		return response

	def validate_ip(self, ip):
		print("Validating IP")
		"""Checks for response at given Philips Hue IP address"""
		addr = "http://{}".format(ip)
		try:
			response = r.get(addr).text
			if "hue personal wireless lighting" in response:
				return True
		except r.ConnectionError:
			print("No response from Philips Hue at {}. Finding new Bridge...".format(ip))
			return False

	def get_username(self):
		print("Getting new username")
		"""Get new username"""
		addr = "http://{}/api".format(self.bridge_ip)
		message = {"devicetype":"HueApp"}
		try:
			response = r.post(addr, json=message).json()[0]
		except r.ConnectionError:
			sys.exit("No response received from Philips Hue. Ensure that it is powered and connected to the network.")
		now = time.time()
		if "error" in response:
			if "link button not pressed" in response["error"]["description"]:
				print("Please press the link button on the Philips Hue.")
				while "error" in response and (time.time()-now) < self.timeout:
					response = r.post(addr,json=message).json()[0]
					time.sleep(0.2)
		if "success" in response:
			if "username" in response["success"]:
				self.bridge_username = response["success"]["username"]
				print("Username: {}".format(self.bridge_username))
			else:
				sys.exit("No username obtained from Philips Hue.")
		else:
			sys.exit("No username obtained from Philips Hue.")

	def validate_username(self, name):
		print("Validating username")
		"""Make sure username is valid"""
		addr = "http://{}/api/{}/".format(self.bridge_ip, name)
		response = self.get_response(addr)
		if response.raise_for_status() is None:
			try:
				response = response.json()[0]
			except KeyError:
				print("No bridge error occured during username validation")
		else:
			sys.exit("Bridge error during username validation")
		if "error" in response:
			if "unauthorized user" in response["error"]["description"]:
				print("Invalid username. Getting new username...")
				return False
			else:
				sys.exit("error validating username")
		else:
			return True

	def update_light_status(self, light_id_):
		print("Updating light state")
		addr = "http://{}/api/{}/lights/{}".format(self.bridge_ip, self.bridge_username, light_id_)
		response = self.get_response(addr).json()
		if response.raise_for_status() is None:
			self.lights[light_id_][0] = response["name"]
			self.lights[light_id_][1] = response["state"]["on"]
			self.lights[light_id_][2] = response["state"]["bri"]
			self.lights[light_id_][3] = response["state"]["reachable"]
			print("Updated light{}".format(self.lights[light_id_][0]))
		else:
			sys.exit("Failed updating light status")

	def initialize_lights(self):
		print("Acquiring initial light state")
		addr = "http://{}/api/{}/".format(self.bridge_ip, self.bridge_username)
		response = self.get_response(addr)
		if response.raise_for_status() is None:
			responselights = response.json()["lights"]
			responsegroups = response.json()["groups"]
		else:
			sys.exit("Error getting initial light state")
		for key in responselights:
										# Name of light
										# is the light on?
										# brightness value
										# is the light connected to the bridge
			self.lights.update({key : [ responselights[key]["name"],                \
										responselights[key]["state"]["on"],         \
										responselights[key]["state"]["bri"],        \
										responselights[key]["state"]["reachable"]
								]})

		for key in responsegroups:
			keys_ = responsegroups[key]["lights"]
										# Name of group
										# Copy lights from self.lights into a list that are associated with this group
										# Are all the lights on?
										# Are any lights on?
			self.groups.update({key : [ responsegroups[key]["name"],                \
										[self.lights[i] for i in keys_],            \
										responsegroups[key]["state"]["all_on"],     \
										responsegroups[key]["state"]["any_on"]      \
								]})

	def set_light(self, light_id_, on_state_, brightness_, transitiontime_):
		addr = "http://{}/api/{}/lights/{}/state".format(self.bridge_ip, self.bridge_username, str(light_id_))
		message = {"on":on_state_, "transitiontime":transitiontime_, "bri":brightness_}
		res = r.put(addr, json=message).json()

	def get_light_names(self):
		lightlist_ = dict()
		for key in self.lights:
			lightlist_.update({int(key): key})
			print("{}: {}".format(key, self.lights[key][0]))
			self.lightlist = lightlist_
