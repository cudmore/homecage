# 20180424

# gpio server

from __future__ import print_function
import os, sys, time, json
from datetime import datetime
from collections import OrderedDict
import socket, subprocess # to get host name
import pickle
import redis
import redis_lock

import RPi.GPIO as GPIO
	
class gpioserver(object):
	def __init__(self):
		self.conn = redis.StrictRedis('localhost')
		self.conn.flushdb()

		# information about the server
		self.server = OrderedDict()
		self.server['date'] = ''
		self.server['time'] = ''
		self.server['ip'] = self.whatismyip()
		self.server['hostname'] = socket.gethostname()

		config = self.loadConfigFile()
		self.setRedis("config", config)

		status = {}
		status['isRunning'] = [] # configured in initGPIO()
		status['ledState'] = [] # configured in initGPIO()
		status['lastAction'] = ""
		self.setRedis('status', status)		

		# dict to convert polarity string to number, e.g. self.polarity['rising'] yields GPIO.RISING
		self.polarity = { 'rising': GPIO.RISING, 'falling': GPIO.FALLING, 'both': GPIO.BOTH}
		
		self.initGPIO() # uses both config and status
		
	def loadConfigFile(self):
		with open('config.json') as configFile:
			config = json.load(configFile, object_pairs_hook=OrderedDict)
		return config

	def initGPIO(self):
		status = self.getRedis('status')
		config = self.getRedis('config')

		# init gpio pins
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)

		'''for debugging i am wiring leds back into triggers, make sure we init leds first'''
		# LEDs (out)
		if config['hardware']['ledPins']:
			for pin in config['hardware']['ledPins']:
				status['ledState'].append(False)
				GPIO.setup(pin, GPIO.OUT)
				GPIO.output(pin, False)

		# triggers, triggerIn is a list of dict [{name:"", pin:<int>, polarity:""}, ...]
		if config['hardware']['triggerIn']:
			print('configuring triggerIn')
			for idx,trigger in enumerate(config['hardware']['triggerIn']):
				GPIO.setup(trigger['pin'], GPIO.IN)
				# pin is always passed as first argument, this is why we have undefined 'x' here
				cb = lambda x, arg1=idx, arg2=trigger['name']: self.triggerIn_Callback(x,arg1,arg2)
				polarity = self.polarity[trigger['polarity']]
				GPIO.add_event_detect(trigger['pin'], polarity, callback=cb, bouncetime=200) # ms
				status['isRunning'].append(False)
				print('   ', idx, 'name:', trigger['name'], 'pin:', trigger['pin'], 'polarity:', trigger['polarity'])
				
		# events in (e.g. frame)
		if config['hardware']['eventIn']:
			print('configuring eventIn')
			for idx,eventIn in enumerate(config['hardware']['eventIn']):
				GPIO.setup(eventIn['pin'], GPIO.IN)
				# pin is always passed as first argument, this is why we have undefined 'x' here
				cb = lambda x, arg1=idx, arg2=eventIn['name']: self.eventIn_Callback(x,arg1,arg2)
				polarity = self.polarity[eventIn['polarity']]
				GPIO.add_event_detect(eventIn['pin'], polarity, callback=cb, bouncetime=200) # ms
				print('   ', idx, 'name:', eventIn['name'], 'pin:', eventIn['pin'], 'polarity:', eventIn['polarity'])
		
		self.setRedis('status', status)
		
	def getRedis(self, key):
		resp = self.conn.get(key)
		if resp is not None:
			return pickle.loads(resp)
		else:
			print('error: getRedis got bad key:', key)
			return None
			
	def setRedis(self, key, value):
		self.conn.set(key, pickle.dumps(value))
			
	def getConfig(self):
		return self.getRedis('config')
		
	def getStatus(self):
		resp = OrderedDict()
		resp['status'] = self.getRedis('status')

		now = datetime.now()
		self.server['date'] = now.strftime('%Y-%m-%d')
		self.server['time'] = now.strftime('%H:%M:%S')

		resp['server'] = self.server
		return resp
		
	def triggerIn_Callback(self, pin, idx, name):
		now = time.time()
		print('triggerIn_Callback() idx:', idx, 'name:', name, 'pin:', pin)
		try:
			with redis_lock.Lock(self.conn, "startpin_callback_lock"):
				print(os.getpid(), 'got the lock', now)
				status = self.getRedis('status')
				if status['isRunning'][idx]:
					print('   already running')
				else:
					print('   starting idx:', idx)
					status['isRunning'][idx] = True
					self.setRedis("status", status)
		except:
			print(os.getpid(), '*** did not get the lock')
			
	def eventIn_Callback(self, pin):
		now = time.time()
		print('eventIn_Callback() pin:', pin)
		
	# turn led on/off
	def led(self, ledNum, on):
		# ledNum is index number 0,1,2,... it is not pin number
		status = self.getRedis('status')
		config = self.getRedis('config')
		numLED = len(config['hardware']['ledPins'])
		if ledNum > numLED-1:
			status['lastAction'] = 'error: led number ' + str(ledNum) + ' is not valid'
		else:
			GPIO.output(config['hardware']['ledPins'][ledNum], on)
			status['ledState'][ledNum] = on
			status['lastAction'] = 'led num ' + str(ledNum) + ' is ' + str(on)
		self.setRedis('status', status)

	# Utility
	def whatismyip(self):
		arg='ip route list'
		p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
		data = p.communicate()
		split_data = data[0].split()
		ipaddr = split_data[split_data.index('src')+1]
		return ipaddr

			
if __name__ == '__main__':
	print('gpioserver main')
	mygpio = gpioserver()
	#print(json.dumps(mygpio.config, indent=4, sort_keys=True))
	
	#
	mygpio.led(0,True)
	time.sleep(1) # seconds
	mygpio.led(0,False)
	time.sleep(1) # seconds
	mygpio.led(0,True)
	time.sleep(1) # seconds
	#
	mygpio.led(1,True)
	time.sleep(1) # seconds
	
		