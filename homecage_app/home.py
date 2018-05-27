'''
Author: Robert Cudore
Date: 20171103

To Do:frameIn
	- add watermark on top of video when we receive a frame
	- write a proper trial class
'''

from __future__ import print_function    # (at top of module)

import os, sys, time, math, io
import subprocess
import threading
from datetime import datetime
from collections import OrderedDict
import json

import RPi.GPIO as GPIO
import picamera

import logging
logger = logging.getLogger('flask.app')

# load dht temperature/humidity sensor library
g_dhtLoaded = 0
try:
	import Adafruit_DHT 
	g_dhtLoaded = 1
except:
	g_dhtLoaded = 0
	logger.warning('Did not load Adafruit_DHT')

import bUtil # to get system info and drive space
from bTrial import bTrial
from bCamera import bCamera

#########################################################################
class home:
	# dict to convert polarity string to number, e.g. self.polarity['rising'] yields GPIO.RISING
	polarityDict_ = { 'rising': GPIO.RISING, 'falling': GPIO.FALLING, 'both': GPIO.BOTH}
	pullUpDownDict = { 'up': GPIO.PUD_UP, 'down': GPIO.PUD_DOWN}

	def __init__(self):
		self.init()

	def init(self):
		logger.debug('start home.init()')
		
		self.config = self.loadConfigFile()
				
		self.trial = bTrial()
		self.camera = bCamera(self.trial)
		# set parameters of camera from config file, be sure to call again when they change
		self.camera.setConfig(self.config) 
		
		# GPIO
		self.initGPIO_()
		
		# save path
		self.videoPath = self.config['video']['savepath']
		self.saveVideoPath = '' # set when we start video recording
		if not os.path.isdir(self.videoPath):
			os.makedirs(self.videoPath)
					
		self.lastResponse = ''
				
		#
		# temperature and humidity
		self.lastTemperatureTime = 0
		self.lastTemperature = None
		self.lastHumidity = None
		
		if self.config['hardware']['readtemperature']:
			if g_dhtLoaded:
				logger.debug('Initialized DHT temperature sensor')
				GPIO.setup(self.config['hardware']['temperatureSensor'], GPIO.IN)
				myThread = threading.Thread(target = self.tempThread)
				myThread.daemon = True
				myThread.start()
			else:
				logger.debug('Did not load DHT temperature sensor')
			
		#
		# system information
		self.systemInfo = bUtil.getSystemInfo()
		
	@property
	def state(self):
		return self.camera.state
		
	def isState(self, thisState):
		''' Return True if self.state == thisState'''
		#return True if self.state==thisState else False
		return True if self.camera.state==thisState else False
		
	def initGPIO_(self):
		''' init gpio pins '''
		# not sure if this is a good idea
		'''
		try:
			GPIO.cleanup()
		except RuntimeWarning:
			print('xxxzzz')
			pass
		'''
			
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)

		if self.config['hardware']['triggerIn']['enabled']:
			pin = self.config['hardware']['triggerIn']['pin']
			polarity = self.config['hardware']['triggerIn']['polarity'] # rising, falling, or both
			polarity = home.polarityDict_[polarity]
			pull_up_down = self.config['hardware']['triggerIn']['pull_up_down'] # up or down
			pull_up_down = home.pullUpDownDict[pull_up_down]
			GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)
			GPIO.add_event_detect(pin, polarity, callback=self.triggerIn_Callback, bouncetime=200) # ms
			#logger.info('gpio configured:' + str(self.config['hardware']['triggerIn']))
		else:
			pin = self.config['hardware']['triggerIn']['pin']
			try:
				GPIO.remove_event_detect(pin)
			except:
				print('error in triggerIn remove_event_detect')
				
		if self.config['hardware']['triggerOut']['enabled']:
			pin = self.config['hardware']['triggerOut']['pin']
			#polarity = self.config['scope']['triggerOut']['polarity']
			GPIO.setup(pin, GPIO.OUT)

		# events in (e.g. frame)
		if self.config['hardware']['eventIn']:
			for idx,eventIn in enumerate(self.config['hardware']['eventIn']):
				name = eventIn['name']
				pin = eventIn['pin']
				enabled = eventIn['enabled'] # is it enabled to receive events
				if enabled:
					pull_up_down = eventIn['pull_up_down'] # up or down
					pull_up_down = home.pullUpDownDict[pull_up_down]
					GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)
					# pin is always passed as first argument, this is why we have undefined 'x' here
					cb = lambda x, arg1=name, arg2=enabled, arg3=pin: self.eventIn_Callback(x,arg1, arg1,arg2, arg3)
					# as long as each event is different pin, polarity can be different
					polarity = home.polarityDict_[eventIn['polarity']]
					GPIO.add_event_detect(pin, polarity, callback=cb, bouncetime=200) # ms
					#print('   ', idx, 'name:', name, 'pin:', pin, 'polarity:', polarity)
				else:
					try:
						GPIO.remove_event_detect(pin)
					except:
						print('error in trieventInggerIn remove_event_detect')
				
		# events out (e.g. led, motor, or lick port)
		if self.config['hardware']['eventOut']:
			for idx,eventOut in enumerate(self.config['hardware']['eventOut']):
				enabled = eventOut['enabled'] # is it enabled to receive events
				pin = eventOut['pin']
				defaultValue = eventOut['defaultValue']
				# set the status in the config struct
				self.config['hardware']['eventOut'][idx]['state'] = defaultValue # so javascript can read state
				self.config['hardware']['eventOut'][idx]['idx'] = idx # for reverse lookup
				#
				if enabled:
					GPIO.setup(pin, GPIO.OUT)
					GPIO.output(pin, defaultValue)

	##########################################
	# Input pin callbacks
	##########################################
	def eventIn_Callback(self, name, enabled=None, pin=None):
		''' Can call manually with just name '''
		now = time.time()
		if pin is None:
			# called by user, look up event in list by ['name']
			dictList = self.config['hardware']['eventIn']
			thisItem = (item for item in dictList if item["name"] == name).next()
			if thisItem is None:
				#error
				pass
			else:
				enabled = thisItem['enabled']
				pin = thisItem['pin']
		if enabled:
			#print('eventIn_Callback() enabled:' + str(enabled) + ' pin:' + str(pin) + ' name:' + name)

			if name == 'frame':
				if self.trial.isRunning:
					self.trial.numFrames += 1
					self.trial.newEvent('frame', self.trial.numFrames, now=now)
					if self.camera:
						self.camera.annotate(self.trial.numFrames)
			if name == 'otherEvent':
				pass

	def triggerIn_Callback(self, pin):
		now = time.time()
		self.camera.startArmVideo(now=now)
		#logger.debug("triggerIn_Callback finished trial:" + str(self.trial['frameNum']))
				
	##########################################
	# Output pins on/off
	##########################################
	def eventOut(self, name, onoff):
		''' turn output pins on/off '''
		dictList = self.config['hardware']['eventOut'] # list of event out(s)
		try:
			thisItem = (item for item in dictList if item["name"] == name).next()
		except StopIteration:
			thisItem = None
		if thisItem is None:
			err = 'eventOut() got bad name: ' + name
			logger.error(err)
			self.lastResponse = err
		else:
			pin = thisItem['pin']
			GPIO.output(pin, onoff)
			# set the state of the out pin we just set
			wasThis = self.config['hardware']['eventOut'][thisItem['idx']]['state']
			if wasThis != onoff:
				self.config['hardware']['eventOut'][thisItem['idx']]['state'] = onoff
				self.trial.newEvent(name, onoff, now=time.time())
				logger.debug('eventOut ' + name + ' '+ str(onoff))

	##########################################
	# Config, loaded from and saved to config.json
	##########################################
	def setParam(self, param, value):
		logger.debug(param + ' ' + str(value))
		one, two = param.split('.')
		if one not in self.config:
			# error
			print('ERROR: setParam() did not find', one, 'in self.config')
			return
		if two not in self.config[one]:
			# error
			print('ERROR: setParam() did not find', two, 'in self.config["', one, '"]')
			return
			
		theType = type(self.config[one][two])
		if theType == str:
			value = str(value)
		if theType == int:
			if value == 'null':
				# we are getting empty values as user types
				return
			value = int(value)
		if theType == bool:
			if value == 'false':
				value = False
			if value == 'true':
				value = True
			value = bool(value)
		# set
		self.config[one][two] = value
		
		# IMPORTANT: update camera config parameters
		self.camera.setConfig(self.config) 
		
		self.lastResponse = one + ' ' + two + ' is now ' + str(value)
		
	def loadConfigDefaultsFile(self):
		logger.debug('loadConfigDefaultsFile')
		with open('config_defaults.json') as configFile:
			try:
				config = json.load(configFile, object_pairs_hook=OrderedDict)
			except ValueError, e:
				logger.error('config_defaults.json ValueError: ' + str(e))
				self.lastResponse = 'Error loading default options file: ' + str(e)
			else:
				self.config = config
				self.initGPIO_()
				# IMPORTANT: update camera config parameters
				self.camera.setConfig(self.config) 
				self.lastResponse = 'Loaded default options file'

	def loadConfigFile(self):
		logger.debug('loadConfigFile')
		with open('config.json') as configFile:
			try:
				config = json.load(configFile, object_pairs_hook=OrderedDict)
			except ValueError, e:
				logger.error('config.json ValueError: ' + str(e))
				sys.exit(1)
			else:
				return config
	
	def saveConfigFile(self):
		logger.debug('saveConfigFile')
		with open('config.json', 'w') as outfile:
			json.dump(self.config, outfile, indent=4)
		self.lastResponse = 'Saved options file'
	
	def getConfig(self):
		# parameters that can be set by user
		return self.config
		
	##########################################
	# Status, real-time
	##########################################
	def getStatus(self):
		'''
		Return the status of the server, all params
		Is called at a short interval, ~1 sec
		'''
						
		status = OrderedDict()
		
		status['server'] = OrderedDict()
		status['server']['state'] = self.camera.state
		status['server']['currentFile'] = self.camera.currentFile
		status['server']['lastResponse'] = self.lastResponse # filled in by each route

		# need to make a dict so javascript can read off which eventOut is on/off
		status['server']['eventOut'] = OrderedDict()
		for eventOut in self.config['hardware']['eventOut']:
			if 'state' in eventOut:
				status['server']['eventOut'][eventOut['name']] = eventOut['state']
			
		#status['trial'] = self.trial.trial
		status['server']['trialElapsedSec'] = self.trial.timeElapsed
		status['server']['epochElapsedSec'] = self.trial.epochTimeElapsed
		status['server']['currentEpoch'] = self.trial.currentEpoch
		
		# temperature and humidity
		status['server']['environment'] = OrderedDict()
		status['server']['environment']['temperature'] = self.lastTemperature
		status['server']['environment']['humidity'] = self.lastHumidity
			
		# system status (ip, host, cpu temperature, drive space remaining, etc)
		#todo: add a web button to refresh this self.drivespaceremaining()		'''
		status['system'] = OrderedDict()
		for k, v in self.systemInfo.iteritems():
			status['system'][k] = v
		now = datetime.now()
		status['system']['date'] = now.strftime('%Y-%m-%d')
		status['system']['time'] = now.strftime('%H:%M:%S')

		return status

	##########################################
	# Start and stop video, stream, arm
	##########################################
	def stop(self):
		logger.debug('stop')
		self.record(0)
		self.stream(0)
		self.stopArmVideo()
		self.trial.stopTrial()
		if self.isState('idle'):
			self.lastResponse = 'Idle'
			
	def record(self, onoff):
		self.camera.record(onoff)
		if self.isState('recording'):
			myThread = threading.Thread(target = self.lightsThread)
			myThread.daemon = True
			myThread.start()

		if self.isState('recording'):
			self.lastResponse = 'Started recording'
		elif self.isState('idle'):
			self.lastResponse = 'Stopped recording'

	def stream(self, onoff):
		self.camera.stream(onoff)
		if self.isState('streaming'):
			self.lastResponse = 'Started streaming'
		elif self.isState('idle'):
			self.lastResponse = 'Stopped streaming'

	def arm(self, onoff):
		self.camera.arm(onoff)
		if self.isState('armed'):
			self.lastResponse = 'Started arm, waiting for trigger in'
		elif self.isState('idle'):
			self.lastResponse = 'Stopped arm'

	def startArmVideo(self, now=time.time()):
		self.camera.startArmVideo(now=now)
		if self.isState('armedrecording'):
			self.lastResponse = 'Started armed video recording'
		
	def stopArmVideo(self):
		self.camera.stopArmVideo()
		if self.isState('idle'):
			self.lastResponse = 'Stopped armed video recording'

	##########################################
	# Background threads
	##########################################
	# todo: merge into lightsThread() function
	def controlLights(self):
		# control lights during recording
		if self.config['lights']['auto']:
			now = datetime.now()
			isDaytime = now.hour > self.config['lights']['sunrise'] and now.hour < self.config['lights']['sunset']
			if isDaytime:
				self.eventOut('whiteLED', True)
				self.eventOut('irLED', False)
			else:
				self.eventOut('whiteLED', False)
				self.eventOut('irLED', True)

	def lightsThread(self):
		logger.debug('lightsThread start')
		while self.isState('recording'):
			self.controlLights()
			time.sleep(.05)
		logger.debug('lightsThread stop')

	def tempThread(self):
		# thread to run temperature/humidity in background
		# dht is blocking, long delay cause delays in web interface
		logger.info('tempThread() start')
		temperatureInterval = self.config['hardware']['temperatureInterval'] # seconds
		pin = self.config['hardware']['temperatureSensor']
		while True:
			if g_dhtLoaded:
				if time.time() > self.lastTemperatureTime + temperatureInterval:
					try:
						humidity, temperature = Adafruit_DHT.read(Adafruit_DHT.DHT22, pin)
						if humidity is not None and temperature is not None:
							self.lastTemperature = math.floor(temperature * 100) / 100
							self.lastHumidity = math.floor(humidity * 100) / 100
							# log this to a file
							self.trial.newEvent('temperature', self.lastTemperature, now=time.time())
							self.trial.newEvent('humidity', self.lastHumidity, now=time.time())
							logger.debug('temperature/humidity ' + str(self.lastTemperature) + '/' + + str(self.lastHumidity))
						else:
							logger.warning('temperature/humidity error')
						# set even on fail, this way we do not immediately hit it again
						self.lastTemperatureTime = time.time()
					except:
						print('readTemperature() exception reading temperature/humidity')
			time.sleep(0.5)
		logger.info('tempThread() stop')

	'''
	# generate a file list of video files
	def make_tree(self, path):
		filelist = []
		for root, dirs, files in os.walk(path):
			for file in files:
				if file.endswith('.h264'):
					filelist.append(file)
		return filelist
	'''
