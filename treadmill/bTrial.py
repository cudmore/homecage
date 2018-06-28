# Robert H Cudmore
# 20180525

import os, sys, time, json, threading, queue
from collections import OrderedDict
from datetime import datetime, timedelta
from pprint import pprint
import RPi.GPIO as GPIO

import logging
logger = logging.getLogger('flask.app')

# load dht temperature/humidity sensor library
g_dhtLoaded = 0
try:
	import Adafruit_DHT 
	g_dhtLoaded = 1
	logger.debug('Succesfully loaded Adafruit_DHT')
except:
	g_dhtLoaded = 0
	logger.warning('Did not load Adafruit_DHT')

from bCamera import bCamera
from bUtil import hostname

#########################################################################
class bTrial:
	# dict to convert polarity string to number, e.g. self.polarity['rising'] yields GPIO.RISING
	polarityDict_ = { 'rising': GPIO.RISING, 'falling': GPIO.FALLING, 'both': GPIO.BOTH}
	pullUpDownDict = { 'up': GPIO.PUD_UP, 'down': GPIO.PUD_DOWN}
	dhtSensorDict_ = { 'DHT11': Adafruit_DHT.DHT11, 'DHT22': Adafruit_DHT.DHT22, 'AM2302': Adafruit_DHT.DHT22}

	def __init__(self):

		self.config = self.loadConfigFile()
		
		if self.config['video']['useCamera']:
			self.cameraErrorQueue = queue.Queue()
			self.camera = bCamera(trial=self, cameraErrorQueue=self.cameraErrorQueue)
		else:
			self.cameraErrorQueue = None
			self.camera = None
				
		self.hostname = hostname()
		
		#
		# GPIO
		self.initGPIO_()

		#
		# runtime
		self.runtime = OrderedDict()

		self.runtime['trialNum'] = 0
		self.runtime['isRunning'] = False
		self.runtime['startTimeSeconds'] = None
		self.runtime['startDateStr'] = ''
		self.runtime['startTimeStr'] = ''

		self.runtime['currentEpoch'] = None
		self.runtime['lastEpochSeconds'] = None # start time of epoch

		self.runtime['eventTypes'] = []
		self.runtime['eventValues'] = []
		self.runtime['eventStrings'] = []
		self.runtime['eventTimes'] = [] # relative to self.runtime['startTimeSeconds']

		self.runtime['currentFile'] = ''
		self.runtime['lastStillTime'] = None

		self.runtime['lastResponse'] = 'None'
		
	#########################################################################
	# property
	#########################################################################
	@property
	def lastResponse(self):
		return self.runtime['lastResponse']
	
	@lastResponse.setter
	def lastResponse(self, str):
		self.runtime['lastResponse'] = str

	@property
	def isRunning(self):
		return self.runtime['isRunning']

	@property
	def timeElapsed(self):
		""" Time elapsed since startTimeSeconds """
		if self.isRunning:
			return round(time.time() - self.runtime['startTimeSeconds'], 2)
		else:
			return None
	
	@property
	def epochTimeElapsed(self):
		if self.isRunning:
			return round(time.time() - self.runtime['lastEpochSeconds'], 1)
		else:
			return None
			
	@property
	def numFrames(self):
		return self.runtime['eventTypes'].count('frame')

	@property
	def currentEpoch(self):
		#return self.runtime['eventTypes'].count('epoch')
		return self.runtime['currentEpoch']
		
	"""
	@property
	def startTimeSeconds(self):
		return self.runtime['startTimeSeconds'] # can be None
	"""

	#########################################################################
	# status
	#########################################################################
	def getStatus(self):
		ret = OrderedDict()
		ret['config'] = self.config
		ret['runtime'] = self.runtime

		now = datetime.now()
		ret['runtime']['currentDate'] = now.strftime('%Y-%m-%d')
		ret['runtime']['currentTime'] = now.strftime('%H:%M:%S')

		ret['runtime']['currentFile'] = self.camera.currentFile
		ret['runtime']['secondsElapsedStr'] = self.camera.secondsElapsedStr
		ret['runtime']['cameraState'] = self.camera.state
		return ret
	
	#########################################################################
	# update config, led, animal
	#########################################################################
	def updateConfig(self, configDict):
		"""
		Update self.config (['trial'], ['lights'], ['video'])
		Only update the subset that can be changed by user in javascript configFormController
		Remember, ['motor'] is saved in a different controller, arduinoFormController
		"""
		
		# todo: check the logic works here
		self.runtime['trialNum'] = configDict['trial']['trialNum']
		
		self.config['trial'] = configDict['trial']
		self.config['lights'] = configDict['lights']
		self.config['video'] = configDict['video']
		
		self.config['hardware']['allowArming'] = configDict['hardware']['allowArming']
		self.config['hardware']['serial']['useSerial'] = configDict['hardware']['serial']['useSerial']

	def updateLED(self, configDict):
		self.config['hardware']['eventOut'][0]['state'] = configDict['hardware']['eventOut'][0]['state']
		self.config['hardware']['eventOut'][1]['state'] = configDict['hardware']['eventOut'][1]['state']
		
	def updateAnimal(self, configDict):
		self.config['trial']['animalID'] = configDict['trial']['animalID']
		self.config['trial']['conditionID'] = configDict['trial']['conditionID']
		
	#########################################################################
	# load and save config file
	#########################################################################
	def loadConfigFile(self):
		logger.debug('loadConfigFile')
		# full path to folder *this file lives in
		mypath = os.path.abspath(os.path.dirname(__file__)) # full path to *this file
		configpath = os.path.join(mypath, 'config_trial.json')
		with open(configpath) as configFile:
			try:
				config = json.load(configFile, object_pairs_hook=OrderedDict)
				#config = self.convertConfig_(config)
			except ValueError as e:
				logger.error('config.json ValueError: ' + str(e))
				sys.exit(1)
			else:
				return config

	def saveConfig(self):
		""" Save self.config to a file """
		logger.debug('saveConfig')
		with open('config_trial.json', 'w') as outfile:
			json.dump(self.config, outfile, indent=4)
		self.lastResponse = 'Saved configuration in config_trial.json file'
	
	def getConfig(self, key1, key2):
		""" Get a single config parameter """
		if not key1 in self.config:
			#error
			raise
		else:
			if not key2 in self.config[key1]:
				# error
				raise
			else:
				return self.config[key1][key2]
				
	#########################################################################
	# GPIO
	#########################################################################
	def initGPIO_(self):
		''' init gpio pins '''

		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)

		#
		# trigger in
		if self.config['hardware']['triggerIn']['enabled']:
			pin = self.config['hardware']['triggerIn']['pin']
			polarity = self.config['hardware']['triggerIn']['polarity'] # rising, falling, or both
			polarity = bTrial.polarityDict_[polarity]
			pull_up_down = self.config['hardware']['triggerIn']['pull_up_down'] # up or down
			pull_up_down = bTrial.pullUpDownDict[pull_up_down]
			GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)
			try:
				GPIO.add_event_detect(pin, polarity, callback=self.triggerIn_Callback, bouncetime=200) # ms
			except (RuntimeError) as e:
				logger.warning('triggerIn add_event_detect: ' + str(e))
				pass
			#logger.info('gpio configured:' + str(self.config['hardware']['triggerIn']))
		else:
			pin = self.config['hardware']['triggerIn']['pin']
			try:
				GPIO.remove_event_detect(pin)
			except:
				print('error in triggerIn remove_event_detect')
				
		#
		# trigger out
		if self.config['hardware']['triggerOut']['enabled']:
			pin = self.config['hardware']['triggerOut']['pin']
			#polarity = self.config['scope']['triggerOut']['polarity']
			GPIO.setup(pin, GPIO.OUT)

		#
		# events in (e.g. frame)
		if self.config['hardware']['eventIn']:
			for idx,eventIn in enumerate(self.config['hardware']['eventIn']):
				name = eventIn['name']
				pin = eventIn['pin']
				enabled = eventIn['enabled'] # is it enabled to receive events
				if enabled:
					pull_up_down = eventIn['pull_up_down'] # up or down
					pull_up_down = bTrial.pullUpDownDict[pull_up_down]
					GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)

					# pin is always passed as first argument, this is why we have undefined 'x' here
					cb = lambda x, name=name: self.eventIn_Callback(x,name)

					# as long as each event is different pin, polarity can be different
					polarity = bTrial.polarityDict_[eventIn['polarity']]

					try:
						GPIO.add_event_detect(pin, polarity, callback=cb, bouncetime=10) # ms
						#GPIO.add_event_detect(pin, polarity, callback=self.eventIn_Callback, bouncetime=200) # ms
					except (RuntimeError) as e:
						logger.warning('eventIn add_event_detect: ' + str(e))
						pass
				else:
					try:
						GPIO.remove_event_detect(pin)
					except:
						print('error in trieventInggerIn remove_event_detect')
				
		#
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

		#
		# start a background thread to control the lights
		self.lightsThread = threading.Thread(target = self.lightsThread)
		self.lightsThread.daemon = True
		self.lightsThread.start()

		#
		# start a background thread to read the temperature
		if self.config['hardware']['dhtsensor']['readtemperature']:
			if g_dhtLoaded:
				logger.debug('Initialized DHT temperature sensor')
				sensorPin = self.config['hardware']['dhtsensor']['temperatureSensor']
				GPIO.setup(sensorPin, GPIO.IN) # pins 2/3 have 1K8 pull up resistors
				myThread = threading.Thread(target = self.tempThread)
				myThread.daemon = True
				myThread.start()
			else:
				#logger.debug('Did not load DHT temperature sensor')
				pass
				
	##########################################
	# Input pin callbacks
	##########################################
	#cb = lambda x, name=name: self.eventIn_Callback(x,name)
	def eventIn_Callback(self, pin, name=None):
		"""
		Can call manually with just name
		REMEMBER: DO NOT RUN IN DEBUG MODE !!!!!!!!!!!!!
		"""
		
		now = time.time()
		
		if self.isRunning:
			enabled = False
			dictList = self.config['hardware']['eventIn']
			if pin is None and name is not None:
				# called by user, look up event in list by ['name']
				thisItem = next(item for item in dictList if item["name"] == name)
				if thisItem is None:
					print('ERROR: did not find pin by name:', name)
					pass
				else:
					enabled = thisItem['enabled']
					pin = thisItem['pin']
			elif pin is not None:
				# we received a callback with pin specified
				# look up by pin number
				thisItem = next(item for item in dictList if item["pin"] == pin)
				if thisItem is None:
					#error
					print('ERROR: did not find pin by pin number:', pin)
				else:
					enabled = thisItem['enabled']
					name = thisItem['name']

			pinIsUp = GPIO.input(pin) == 1
			#print('=== RECEIVED eventIn_Callback', now, 'pin:', pin, 'name:', name, 'enabled:', enabled, 'pinIsUp:', pinIsUp)
			
			if enabled:
				#print('eventIn_Callback() enabled:' + str(enabled) + ' pin:' + str(pin) + ' name:' + name)
			
				if name == 'frame':
					#self.numFrames += 1 # can't do this, no setter
					self.newEvent('frame', self.numFrames, now=now)
					if self.camera is not None:
						self.camera.annotate(self.numFrames)
					logger.debug('eventIn_Callback() frame ' + str(numFrames))
				else:
					# just log the name and state
					self.newEvent(name, pinIsUp, now=now)
					if name == 'arduinoMotor':
						if self.camera is not None:
							if pinIsUp:
								self.camera.annotate('m')
							else:
								self.camera.annotate('')
					logger.debug('eventIn_Callback() pin: ' + str(pin) + ' name: ' + name + ' value: ' + str(pinIsUp))

			else:
				logger.warning('eventIn_Callback() pin is not enabled, pin: ' + str(pin) + ' name: ' + name + ' value: ' + str(pinIsUp))
		else:
			#print('!!! Trial not running eventIn_Callback()', now, 'pin:', pin, 'name:', name, self.isRunning)
			pass
						
	def triggerIn_Callback(self, pin):
		now = time.time()
		logger.debug('triggerIn_Callback')
		if self.camera is not None:
			self.camera.startArmVideo(now=now)
			self.lastResponse = self.camera.lastResponse
				
	##########################################
	# Output pins on/off
	##########################################
	def eventOut(self, name, onoff):
		""" Turn output pins on/off """
		dictList = self.config['hardware']['eventOut'] # list of event out(s)
		try:
			# having lots of problems b/w python 2/3 with g.next() versus next(g)
			#thisItem = (item for item in dictList if item["name"] == name).next()
			thisItem = next(item for item in dictList if item["name"] == name)
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
				self.newEvent(name, onoff, now=time.time())
				logger.debug('eventOut ' + name + ' '+ str(onoff))

	#########################################################################
	# start/stop
	#########################################################################
	def startTrial(self, startArmVideo=False, now=None):
		if now is None:
			now = time.time()
			
		if self.isRunning:
			logger.warning('startTrial but trial is running')
			return 0
			
		self.runtime['trialNum'] = self.runtime['trialNum'] + 1
		
		self.runtime['startArmVideo'] = startArmVideo
		
		self.runtime['isRunning'] = True
		
		self.runtime['startTimeSeconds'] = now
		#self.runtime['startTimeStr'] = time.strftime('%Y%m%d_%H%M%S', time.localtime(now)) 
		self.runtime['startDateStr'] = time.strftime('%Y%m%d', time.localtime(now))
		self.runtime['startTimeStr'] = time.strftime('%H:%M:%S', time.localtime(now))
		
		self.runtime['currentEpoch'] = 0
		self.runtime['lastEpochSeconds'] = now
		
		self.runtime['eventTypes'] = []
		self.runtime['eventValues'] = []
		self.runtime['eventStrings'] = []
		self.runtime['eventTimes'] = [] # relative to self.runtime['startTimeSeconds']
		
		self.runtime['currentFile'] = 'n/a' # video
		#todo: is this used
		self.runtime['lastStillTime'] = None
		
		logger.debug('startTrial startArmVideo=' + str(startArmVideo))
		self.newEvent('startTrial', self.runtime['trialNum'], now=now)
		
		if self.camera is not None:
			if startArmVideo:
				# *this function startTrial() is being called from within the startarmvideo loop
				pass
			else:
				self.camera.record(True, startNewTrial=False)
		
	def stopTrial(self):
		# todo: finish up and close trial file
		now = time.time()
		if not self.isRunning:
			logger.warning('stopTrial but trial is not running')
			return 0

		logger.debug('stopTrial')
		self.newEvent('stopTrial', self.runtime['trialNum'], now=now)
		self.runtime['isRunning'] = False
		self.saveTrial()

		if self.runtime['startArmVideo']:
			if self.camera is not None:
				# *this function startTrial() is being called from with the startarmvideo loop
				pass
		else:
			if self.camera is not None:
				self.camera.record(False)
		
	def newEvent(self, type, val, str='', now=None):
		if now is None:
			now = time.time()
		if self.isRunning:
			self.runtime['eventTypes'].append(type)
			self.runtime['eventValues'].append(val)
			self.runtime['eventStrings'].append(str)
			self.runtime['eventTimes'].append(now)
		
	def newEpoch(self, now=None):
		if now is None:
			now = time.time()
		if self.isRunning:
			self.runtime['currentEpoch'] += 1
			self.runtime['lastEpochSeconds'] = now
			self.newEvent('newRepeat', self.currentEpoch, now=now)
		
	def getFilename(self, useStartTime=False, withRepeat=False):
		"""
		Get a base filename from trial
		Caller is responsible for appending proper filetype extension
		"""
		hostnameID_str = ''
		if self.config['trial']['includeHostname']:
			hostnameID_str = '_' + self.hostname # we always have a host name
		animalID_str = ''
		if self.config['trial']['animalID']:
			animalID_str = '_' + self.config['trial']['animalID']
		conditionID_str = ''
		if self.config['trial']['conditionID']:
			conditionID_str = '_' + self.config['trial']['conditionID']
		if useStartTime:
			# time the trial was started
			useThisTime = time.localtime(self.runtime['startTimeSeconds'])
		else:
			# time the epoch was started
			useThisTime = time.localtime(self.runtime['lastEpochSeconds'])
		timeStr = time.strftime('%Y%m%d_%H%M%S', useThisTime) 
		
		# file names have (hostname, animal, condition, trial)
		filename = timeStr + hostnameID_str + animalID_str + conditionID_str + '_t' + str(self.runtime['trialNum'])
		if withRepeat:
			filename += '_r' + str(self.currentEpoch)
		return filename
		
	def saveTrial(self):
		delim = ','
		eol = '\n'
		saveFile = self.getFilename(useStartTime=True) + '.txt'
		savePath = os.path.join('/home/pi/video', self.runtime['startDateStr'])
		saveFilePath = os.path.join(savePath, saveFile)
		if not os.path.exists(savePath):
			os.makedirs(savePath)
		with open(saveFilePath, 'w') as file:
			# one line header
			# todo: clean up numRepeats = ['currentEpoch']
			headerLine = 'date=' + self.runtime['startDateStr'] + ';' \
							'time=' + self.runtime['startTimeStr'] + ';' \
							'startTimeSeconds=' + str(self.runtime['startTimeSeconds']) + ';' \
							'hostname=' + '"' + self.hostname + '"' + ';' \
							'id=' + '"' + self.config['trial']['animalID'] + '"' + ';' \
							'condition=' + '"' + self.config['trial']['conditionID'] + '"' + ';' \
							'trialNum=' + str(self.runtime['trialNum']) + ';' \
							'numRepeats=' + str(self.runtime['currentEpoch']) + ';' \
							'repeatDuration=' + str(self.config['trial']['repeatDuration']) + ';' \
							'numRepeatsRecorded=' + str(self.config['trial']['numberOfRepeats']) + ';' \
							'repeatInfinity=' + '"' + str(self.config['trial']['repeatInfinity']) + '"' + ';'

			if self.camera is not None:
				cameraHeader = 'video_fps=' + str(self.config['video']['fps']) + ';' \
							'video_resolution=' + '"' + self.config['video']['resolution'] + '"' + ';'
				headerLine += cameraHeader
			
			headerLine += eol						
			file.write(headerLine)
			# column header for event data is (date, time, sconds, event, value, str
			columnHeader = 'date' + delim + 'time' + delim + 'seconds' + delim + 'event' + delim + 'value' + delim + 'str' + eol
			file.write(columnHeader)
			# one line per event
			for idx, eventTime in enumerate(self.runtime['eventTimes']):
				# convert epoch seconds to date/time str 
				dateStr = time.strftime('%Y%m%d', time.localtime(eventTime))
				timeStr = time.strftime('%H:%M:%S', time.localtime(eventTime))
				# need the plus at end of each line here
				frameLine = dateStr + delim + \
							timeStr + delim + \
							str(eventTime) + delim + \
							self.runtime['eventTypes'][idx] + delim + \
							str(self.runtime['eventValues'][idx]) + delim + \
							self.runtime['eventStrings'][idx]
				frameLine += eol
				file.write(frameLine)

	#########################################################################
	# NOT WORKING
	#########################################################################
	def loadTrialFile(Self, path):
		"""
		load a .txt trial file
		"""
		ret = OrderedDict()
		ret['recordVideo'] = []
		if not os.path.isfile(path):
			return ret
		with open(path) as f:
			# parse one line header
			header = f.readline().strip()
			print('header 0:', header)
			if header.endswith(';'):
				# print('stripping ; from header', str(len(header)))
				header = header[0:len(header)-1] # python string index uses ':' and not ','
			print('header 1:', header)
			header = header.split(';') # header is a list of k=v
			# print('loadTrialFile() header:', header)
			for item in header:
				lhs,rhs = item.split('=')
				ret[lhs] = rhs
				
			# one line column names
			# todo: parse column names so we don't need to use [idx] below
			columnNames = f.readline().rstrip()
			# list of events, one per line
			event = f.readline().rstrip()
			while event:
				# print('   event:', event)
				event = event.split(',') # event is a list
				for item in event:
					# something like: 20180611,09:03:16,1528722196.370188,recordVideo,/home/pi/video/20180611/20180611_090316_hc1_animal_condition_t1_r2.h264
					itemType = item[3]
					if itemType == 'recordVideo':
						recordVideo = {}
						recordVideo['repeat'] = item[4]
						recordVideo['videoFile'] = item[5]
						ret['recordVideo'].append(recordVideo)
				event = f.readline().rstrip()
		return ret
		
	#############################################################
	# Background threads
	#############################################################
	def lightsThread(self):
		logger.debug('lightsThread start')
		while True:
			if self.config['lights']['auto']:
				now = datetime.now()
				isDaytime = now.hour > float(self.config['lights']['sunrise']) and now.hour < float(self.config['lights']['sunset'])
				if isDaytime:
					self.eventOut('whiteLED', True)
					self.config['hardware']['eventOut'][0]['state'] = True
					
					self.eventOut('irLED', False)
					self.config['hardware']['eventOut'][1]['state'] = False
				else:
					self.eventOut('whiteLED', False)
					self.config['hardware']['eventOut'][0]['state'] = False

					self.eventOut('irLED', True)
					self.config['hardware']['eventOut'][1]['state'] = True

				#print(self.config['hardware']['eventOut'][0]['state'], self.config['hardware']['eventOut'][1]['state'])
				
			time.sleep(.5)
		logger.debug('lightsThread stop')

	def tempThread(self):
		"""
		Thread to run temperature/humidity in background
		Adafruit DHT sensor code is blocking
		"""
		logger.info('tempThread() start')
		lastTemperatureTime = 0
		temperatureInterval = self.config['hardware']['dhtsensor']['temperatureInterval'] # seconds
		continuouslyLog = self.config['hardware']['dhtsensor']['continuouslyLog']
		sensorType = bTrial.dhtSensorDict_[self.config['hardware']['dhtsensor']['sensorType']]
		pin = self.config['hardware']['dhtsensor']['temperatureSensor']
		while True:
			if g_dhtLoaded:
				now = time.time()
				if now > lastTemperatureTime + temperatureInterval:
					try:
						humidity, temperature = Adafruit_DHT.read_retry(sensorType, pin)
						if humidity is not None and temperature is not None:
							lastTemperature = round(temperature, 2)
							lastHumidity = round(humidity, 2)
							# log this to a file
							self.newEvent('temperature', lastTemperature)
							self.newEvent('humidity', lastHumidity)
							#logger.debug('temperature/humidity ' + str(lastTemperature) + '/' + str(lastHumidity))
							if continuouslyLog:
								logFile = 'logs/environment.log'
								if not os.path.isfile(logFile):
									headerLine = "Host,DateTime,Seconds,Temperature,Humidity,whiteLight,irLight" + '\n'
									with open(logFile, 'a') as f:
										f.write(headerLine)
								dateTimeStr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
								secondsStr = str(now)
								lineStr = self.hostname + ',' \
									+ dateTimeStr + ',' \
									+ secondsStr + ',' \
									+ str(lastTemperature) + ',' \
									+ str(lastHumidity) + ',' \
									+ '' + ',' \
									+ '' \
									+ '\n' 
								with open(logFile, 'a') as f:
									f.write(lineStr)
						else:
							logger.warning('temperature/humidity error')
						# set even on fail, this way we do not immediately hit it again
						lastTemperatureTime = time.time()
					except:
						logger.error('exception reading temp/hum')
						raise
			time.sleep(1)
		logger.info('tempThread() stop')
	
if __name__ == '__main__':
	logger = logging.getLogger()
	handler = logging.StreamHandler()
	formatter = logging.Formatter(
			'%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

		
