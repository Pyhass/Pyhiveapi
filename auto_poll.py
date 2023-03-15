from pyhiveapi import Hive, SMS_REQUIRED
import time,sys
import traceback, botocore, json
import requests
from influxdb_client import InfluxDBClient,Point,WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS,ASYNCHRONOUS
from urllib3.exceptions import NewConnectionError,ConnectTimeoutError

"""
Code to test pyhiveapi running autonomously, i.e. not inside Home Assistant
The hive is polled every 60 seconds by default , set by DELAY constant
Additional requirements: influxdb_client
It will optionally upload data to an influxdb v2 bucket

To use from command line:
pip install influxdb_client
python hivetest.py hive_configs.json

"""
DELAY=60  #delay in seconds between polling the Hive

			
class OwnHive(Hive):
	def __init__(
		self,
		username=None,
		password=None,
		device_id=None
			):
		super().__init__(username=username,password=password)
		self.this_device,self.this_name,self.hive_ID=None,None,None
		self.device_id=device_id
		self.startup()
	
	def startup(self):
		self.login()
		self.startSession()
		self.get_device()		
	
	def sensors(self):
		self.createDevices()
		devices=self.deviceList.get('sensor')
		return devices
		
	def get_device(self):
		for device in self.sensors():
			if device['device_id']==self.device_id:
				self.this_device=device
				self.this_name=self.this_device['device_name']
				self.hive_ID=self.this_device['hiveID']
				return
		
	def get_latest(self):
		self.latest={}
		self.latest['temp']=self.heating.getCurrentTemperature(self.this_device)
		self.latest['target']=self.heating.getTargetTemperature(self.this_device)
		data = self.session.data.products[self.hive_ID]['state']
		self.latest['mode']=data['mode']
		self.latest['boost']=data['boost']
		self.latest['frostProtection']=data['frostProtection']
		data = self.session.data.products[self.hive_ID]['props']
		self.latest['online']=data['online']
		self.latest['updated']=self.session.data.devices[HUB_ID].get('lastSeen')
		self.latest['updated_str']=self.epochTime(self.latest['updated']/1000,"%d.%m.%Y %H:%M:%S","from_epoch")

	def save_latest(self):
		influx_write2(
			{
			"hive_id":self.hive_ID,
			"device_id":self.device_id,
			"device_name":self.this_name,
			"mode":self.latest['mode'],
			"boost":self.latest['boost'],
			"online":self.latest['online'],
			},			
			{
			"temp":self.latest['temp'],
			"target":self.latest['target'],
			"updated":self.latest['updated']
			}
			)

	def self_test(self):
		while True:
			if self.getDevices(self.hive_ID):
				self.get_latest()
				print(self.latest)
				time.sleep(60)
			else:
				raise Exception("Failed to update devices")	
		
	def live_run(self):
		while True:		
			try:
				if not self.getDevices(self.hive_ID):
					raise Exception("Failed to update devices")		
				self.get_latest()
				#print(self.latest)
				self.save_latest()
				time.sleep(DELAY)
			except Exception as e:
				try:
					print(f'Failed HIVE call: type: {e} INFO:{sys.exc_info()}') 
#					#try to reauthenticate
					self.startup()
				except Exception as e:
					print(f'Failed to restart: {e}')
# 					raise another exception here if you want to drop out of forever loop
					time.sleep(DELAY)

def getConfigValue(key, defaultValue):
    if key in config:
        return config[key]
    return defaultValue

def load_config(configFilename):
    global INFLUX_URL, BUCKET, ORG, INFLUX_TOKEN,USER,PASSWORD,DEVICE_ID,HUB_ID,config
    config = {}
    with open(configFilename) as configFile:
        config = json.load(configFile)
    
    USER=getConfigValue("USER",None)
    PASSWORD=getConfigValue("PASS",None)
    DEVICE_ID=getConfigValue("DEVICE_ID",None)
    HUB_ID=getConfigValue("HUB_ID",None)
    INFLUX_URL=getConfigValue("INFLUX_URL",None)
    BUCKET=getConfigValue("BUCKET",None)
    ORG=getConfigValue("ORG",None)
    INFLUX_TOKEN=getConfigValue("INFLUX_TOKEN",None)

def influx_write2(tags,fields):
	with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=ORG) as client:
	    write_api = client.write_api(write_options=SYNCHRONOUS)
	    dictionary = {
	    "measurement": "hive_devices",
	    "tags": tags,
	    "fields":fields,
	    }
	    try:
	    	write_api.write(BUCKET, ORG, dictionary)
	    except (NewConnectionError,ConnectTimeoutError):
	    	print("ERROR: Can't reach Influx server. Data not saved.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python {} <config-file>'.format(sys.argv[0]))
    else:
	    configFilename = sys.argv[1]
	    load_config(configFilename)
	    
	    o=OwnHive(username=USER,password=PASSWORD,device_id=DEVICE_ID)
	    o.live_run()
