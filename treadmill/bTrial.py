# Robert H Cudmore
# 20180525

import os, time, json
from collections import OrderedDict
from datetime import datetime, timedelta

import RPi.GPIO as GPIO

import logging
logger = logging.getLogger('flask.app')

from bCamera import bCamera
from bUtil import hostname

#########################################################################
class bTrial:
	# dict to convert polarity string to number, e.g. self.polarity['rising'] yields GPIO.RISING
	polarityDict_ = { 'rising': GPIO.RISING, 'falling': GPIO.FALLING, 'both': GPIO.BOTH}
	pullUpDownDict = { 'up': GPIO.PUD_UP, 'down': GPIO.PUD_DOWN}

	def __init__(self):
		#
		# NEW
		self.config = self.loadConfigFile()
		
		if self.config['video']['useCamera']:
			self.camera = bCamera(trial=self)
		else:
			self.camera = None
			
		self.hostname = hostname()
		
		# GPIO
		self.initGPIO_()

		#
		# OLD
		self.trialNum = 0
		
		self.lastResponse = ''
		
		self.trial = OrderedDict()
		self.trial['isRunning'] = False
		self.trial['startTimeSeconds'] = None
		self.trial['startTimeStr'] = ''
		self.trial['dateStr'] = ''
		self.trial['timeStr'] = ''

		self.trial['trialNum'] = None

		self.trial['currentEpoch'] = None
		self.trial['lastEpochSeconds'] = None # start time of epoch

		self.trial['eventTypes'] = []
		self.trial['eventValues'] = []
		self.trial['eventStrings'] = []
		self.trial['eventTimes'] = [] # relative to self.trial['startTimeSeconds']

		self.trial['currentFile'] = ''
		self.trial['lastStillTime'] = None

		self.trial['animalID'] = ''
		self.trial['conditionID'] = ''
		
		# removed for treadmill
		#self.trial['headerStr'] = ''
		
		# added for treadmill
		self.trial['slave'] = False
	
	def getStatus(self):
		ret = OrderedDict()
		ret['config'] = self.config
		ret['trial'] = self.trial

		now = datetime.now()
		ret['trial']['currentDate'] = now.strftime('%Y-%m-%d')
		ret['trial']['currentTime'] = now.strftime('%H:%M:%S')

		ret['trial']['cameraState'] = self.camera.state
		return ret
		
	#########################################################################
	# GPIO
	#########################################################################
	def initGPIO_(self):
		''' init gpio pins '''

		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)

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
					pull_up_down = bTrial.pullUpDownDict[pull_up_down]
					GPIO.setup(pin, GPIO.IN, pull_up_down=pull_up_down)
					# pin is always passed as first argument, this is why we have undefined 'x' here
					cb = lambda x, arg1=name, arg2=enabled, arg3=pin: self.eventIn_Callback(x,arg1, arg1,arg2, arg3)
					# as long as each event is different pin, polarity can be different
					polarity = bTrial.polarityDict_[eventIn['polarity']]
					try:
						GPIO.add_event_detect(pin, polarity, callback=cb, bouncetime=200) # ms
					except (RuntimeError) as e:
						logger.warning('eventIn add_event_detect: ' + str(e))
						pass
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
			# having lots of problems b/w python 2/3 with g.next() versus next(g)
			#thisItem = (item for item in dictList if item["name"] == name).next()
			thisItem = next(item for item in dictList if item["name"] == name)
			if thisItem is None:
				#error
				pass
			else:
				enabled = thisItem['enabled']
				pin = thisItem['pin']
		if enabled:
			#print('eventIn_Callback() enabled:' + str(enabled) + ' pin:' + str(pin) + ' name:' + name)

			if name == 'frame':
				if self.isRunning:
					#self.numFrames += 1 # can't do this, no setter
					self.newEvent('frame', self.numFrames, now=now)
					if self.camera is not None:
						self.camera.annotate(self.numFrames)
			if name == 'otherEvent':
				pass

	def triggerIn_Callback(self, pin):
		now = time.time()
		if self.camera is not None:
			self.camera.startArmVideo(now=now)
			self.lastResponse = self.camera.lastResponse
				
	##########################################
	# Output pins on/off
	##########################################
	def eventOut(self, name, onoff):
		''' turn output pins on/off '''
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
	# config
	#########################################################################
	def loadConfigFile(self):
		logger.debug('loadConfigFile')
		# full path to folder *this file lives in
		mypath = os.path.abspath(os.path.dirname(__file__)) # full path to *this file
		configpath = os.path.join(mypath, 'config_trial.json')
		with open(configpath) as configFile:
			try:
				config = json.load(configFile, object_pairs_hook=OrderedDict)
				config = self.convertConfig_(config)
			except ValueError as e:
				logger.error('config.json ValueError: ' + str(e))
				sys.exit(1)
			else:
				return config

	def convertConfig_(self, config):
		'''
		This is shitty, saving json is converting everything to string (sometimes).
		We need to manually convert some values back to float/int
		'''
		config['video']['fileDuration'] = float(config['video']['fileDuration'])
		config['video']['numberOfRepeats'] = int(config['video']['numberOfRepeats'])
		config['video']['fps'] = int(config['video']['fps'])
		config['video']['stillInterval'] = float(config['video']['stillInterval'])
	
		config['lights']['sunset'] = float(config['lights']['sunset'])
		config['lights']['sunrise'] = float(config['lights']['sunrise'])

		return config

	#########################################################################
	# start/stop
	#########################################################################
	#def startTrial(self, headerStr='', now=None):
	def startTrial(self, slave=False, now=None):
		if now is None:
			now = time.time()
			
		self.trialNum += 1
		
		# removed for treadmill
		#self.trial['headerStr'] = headerStr

		self.trial['slave'] = slave
		
		self.trial['isRunning'] = True
		self.trial['startTimeSeconds'] = now
		self.trial['startTimeStr'] = time.strftime('%Y%m%d_%H%M%S', time.localtime(now)) 
		self.trial['dateStr'] = time.strftime('%Y%m%d', time.localtime(now))
		self.trial['timeStr'] = time.strftime('%H:%M:%S', time.localtime(now))

		self.trial['trialNum'] = self.trialNum
		
		self.trial['currentEpoch'] = 0
		self.trial['lastEpochSeconds'] = now
		
		self.trial['eventTypes'] = []
		self.trial['eventValues'] = []
		self.trial['eventStrings'] = []
		self.trial['eventTimes'] = [] # relative to self.trial['startTimeSeconds']
		
		self.trial['currentFile'] = 'n/a' # video
		self.trial['lastStillTime'] = None
		
		logger.debug('startTrial')
		self.newEvent('startTrial', self.trialNum, now=now)
		
		if not self.trial['slave'] and self.camera is not None:
			self.camera.record(True)
		
	def stopTrial(self):
		# todo: finish up and close trial file
		now = time.time()
		if self.isRunning:
			logger.debug('stopTrial')
			self.newEvent('stopTrial', self.trialNum, now=now)
			self.trial['isRunning'] = False
			self.saveTrial()

			if not self.trial['slave'] and self.camera is not None:
				self.camera.record(False)
		
	def newEvent(self, type, val, str='', now=None):
		if now is None:
			now = time.time()
		if self.isRunning:
			self.trial['eventTypes'].append(type)
			self.trial['eventValues'].append(val)
			self.trial['eventStrings'].append(str)
			self.trial['eventTimes'].append(now)
		
	def newEpoch(self, now=None):
		if now is None:
			now = time.time()
		if self.isRunning:
			self.trial['currentEpoch'] += 1
			self.trial['lastEpochSeconds'] = now
			self.newEvent('newRepeat', self.currentEpoch, now=now)
			#print('newEpoch:', self.trial['currentEpoch'], self.trial['lastEpochSeconds'])
		
	def getFilename(self, useStartTime=False, withRepeat=False):
		'''
		Get a base filename from trial
		Caller isresponsible for appending proper filetype extension
		'''
		hostnameID_str = '_' + self.hostname # we always have a host name
		animalID_str = ''
		if self.trial['animalID']:
			animalID_str = '_' + self.trial['animalID']
		conditionID_str = ''
		if self.trial['conditionID']:
			conditionID_str = '_' + self.trial['conditionID']
		# time is the time the epoch was started
		if useStartTime:
			useThisTime = time.localtime(self.trial['startTimeSeconds'])
		else:
			useThisTime = time.localtime(self.trial['lastEpochSeconds'])
		timeStr = time.strftime('%Y%m%d_%H%M%S', useThisTime) 
		
		# file names will always have (hostname, animal, condition, trial)
		filename = timeStr + hostnameID_str + animalID_str + conditionID_str + '_t' + str(self.trialNum)
		if withRepeat:
			filename += '_r' + str(self.currentEpoch)
		return filename
		
	def saveTrial(self):
		delim = ','
		eol = '\n'
		saveFile = self.getFilename(useStartTime=True) + '.txt'
		savePath = os.path.join('/home/pi/video', self.trial['dateStr'])
		saveFilePath = os.path.join(savePath, saveFile)
		if not os.path.exists(savePath):
			os.makedirs(savePath)
		dateStr = self.trial['dateStr']
		timeStr = self.trial['timeStr']
		fakeNow = ''
		with open(saveFilePath, 'w') as file:
			# one line header
			headerLine = 'date=' + self.trial['dateStr'] + ';' \
							'time=' + self.trial['timeStr'] + ';' \
							'startTimeSeconds=' + str(self.trial['startTimeSeconds']) + ';' \
							'hostname=' + '"' + self.hostname + '"' + ';' \
							'id=' + '"' + self.trial['animalID'] + '"' + ';' \
							'condition=' + '"' + self.trial['conditionID'] + '"' + ';' \
							'trialNum=' + str(self.trial['trialNum']) + ';' \
							'numRepeats=' + str(self.trial['currentEpoch']) + ';'
			if self.camera is not None:
				cameraHeader = self.camera.getHeaderStr()
				headerLine += cameraHeader
			'''
			if self.trial['headerStr']:
				headerLine += self.trial['headerStr']
			'''
			headerLine += eol
			
			file.write(headerLine)
			# column header for event data is (date, time, sconds, event, value, str
			columnHeader = 'date' + delim + 'time' + delim + 'seconds' + delim + 'event' + delim + 'value' + delim + 'str' + eol
			file.write(columnHeader)
			# one line per event
			for idx, eventTime in enumerate(self.trial['eventTimes']):
				# convert epoch seconds to date/time str 
				dateStr = time.strftime('%Y%m%d', time.localtime(eventTime))
				timeStr = time.strftime('%H:%M:%S', time.localtime(eventTime))
				# need the plus at end of each line here
				frameLine = dateStr + delim + \
							timeStr + delim + \
							str(eventTime) + delim + \
							self.trial['eventTypes'][idx] + delim + \
							str(self.trial['eventValues'][idx]) + delim + \
							self.trial['eventStrings'][idx]
				frameLine += eol
				file.write(frameLine)

	def loadTrialFile(Self, path):
		'''
		load a .txt trial file
		'''
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
		
	@property
	def isRunning(self):
		return self.trial['isRunning']

	@property
	def timeElapsed(self):
		''' time elapsed since startTimeSeconds '''
		if self.isRunning:
			return round(time.time() - self.trial['startTimeSeconds'], 2)
		else:
			return None
	
	@property
	def epochTimeElapsed(self):
		if self.isRunning:
			return round(time.time() - self.trial['lastEpochSeconds'], 1)
		else:
			return None
			
	@property
	def numFrames(self):
		return self.trial['eventTypes'].count('frame')

	@property
	def currentEpoch(self):
		#return self.trial['eventTypes'].count('epoch')
		return self.trial['currentEpoch']
		
	@property
	def startTimeSeconds(self):
		return self.trial['startTimeSeconds'] # can be None

	@property
	def animalID(self):
		return self.trial['animalID'] # can be None

	@property
	def conditionID(self):
		return self.trial['conditionID'] # can be None

if __name__ == '__main__':
	logger = logging.getLogger()
	handler = logging.StreamHandler()
	formatter = logging.Formatter(
			'%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

		
