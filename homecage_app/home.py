'''
Author: Robert Cudore
Date: 20171103

To Do:
	- add watermark on top of video when we receive a frame
	- write a proper trial class
'''

from __future__ import print_function    # (at top of module)

import os, time, math, io
import subprocess
import threading
from datetime import datetime
from collections import OrderedDict
import json
import socket # to get hostname

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

class trial:
	def __init__(self):
		self.trialNum = 0
		
		self.trial = OrderedDict()
		self.trial['isRunning'] = False
		self.trial['startTimeSeconds'] = None
		self.trial['startTimeStr'] = ''
		self.trial['dateStr'] = ''
		self.trial['timeStr'] = ''

		self.trial['trialNum'] = None

		self.trial['lastEpochSeconds'] = None

		self.trial['eventTypes'] = []
		self.trial['eventValues'] = []
		self.trial['eventTimes'] = [] # relative to self.trial['startTimeSeconds']

		self.trial['currentFile'] = ''
		self.trial['lastStillTime'] = None
		
	def startTrial(self, now=time.time()):
		logger.debug('startTrial now:' + str(now))
		self.trialNum += 1
		
		self.trial['isRunning'] = True
		self.trial['startTimeSeconds'] = now
		self.trial['startTimeStr'] = time.strftime('%Y%m%d_%H%M%S', time.localtime(now)) 
		self.trial['dateStr'] = time.strftime('%Y%m%d', time.localtime(now))
		self.trial['timeStr'] = time.strftime('%H:%M:%S', time.localtime(now))

		self.trial['trialNum'] = self.trialNum
		
		self.trial['lastEpochSeconds'] = now
		
		self.trial['eventTypes'] = []
		self.trial['eventValues'] = []
		self.trial['eventTimes'] = [] # relative to self.trial['startTimeSeconds']
		
		self.trial['currentFile'] = 'n/a' # video
		self.trial['lastStillTime'] = None
		
		# trials always start with an epoch
		#self.newEpoch(now)
		
	def stopTrial(self):
		# todo: finish up and close trial file
		logger.debug('stopTrial')
		self.trial['isRunning'] = False
		self.saveTrial()
		'''
		try:
			#self.camera.annotate_background = picamera.Color('black')
			self.camera.annotate_text = ''
		except PiCameraClosed as e:
			print(e)
		'''
		
	def newEvent(self, type, val, now=time.time()):
		if self.isRunning:
			self.trial['eventTypes'].append(type)
			self.trial['eventValues'].append(val)
			self.trial['eventTimes'].append(now)
		
	def newEpoch(self, now=time.time()):
		if self.isRunning:
			self.trial['lastEpochSeconds'] = now
			self.newEvent('epoch', self.numEpochs + 1, now=now)
		
	def saveTrial(self):
		delim = ','
		eol = '\n'
		saveFile = self.trial['startTimeStr'] + '_t' + str(self.trialNum) + '.txt'
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
							'trialNum=' + str(self.trial['trialNum']) + ';' \
							'numEpochs=' + str(self.numEpochs) + eol
			file.write(headerLine)
			# column header for event data
			columnHeader = 'date' + delim + 'time' + delim + 'seconds' + delim + 'event' + delim + 'value' + eol
			file.write(columnHeader)
			# one line per frame
			for idx, eventTime in enumerate(self.trial['eventTimes']):
				# need ths plus at end of each line here
				frameLine = self.trial['dateStr'] + delim + \
							self.trial['timeStr'] + delim + \
							str(eventTime) + delim + \
							self.trial['eventTypes'][idx] + delim + \
							str(self.trial['eventValues'][idx]) + eol
				file.write(frameLine)

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
			return round(time.time() - self.trial['lastEpochSeconds'], 2)
		else:
			return None
			
	@property
	def numFrames(self):
		return self.trial['eventTypes'].count('frame')
	@property
	def numEpochs(self):
		return self.trial['eventTypes'].count('epoch')
		
	@property
	def startTimeSeconds(self):
		return self.trial['startTimeSeconds'] # can be None

class camera:
	def __init__(self):
		self.camera = None
	def annotate(self, str):
		try:
			#self.camera.annotate_background = picamera.Color('black')
			self.camera.annotate_text = ''
		except PiCameraClosed as e:
			print(e)
		
class home:
	def __init__(self):
		self.init()

	def init(self):
		logger.debug('start home.init()')
		
		# dict to convert polarity string to number, e.g. self.polarity['rising'] yields GPIO.RISING
		self.polarityDict_ = { 'rising': GPIO.RISING, 'falling': GPIO.FALLING, 'both': GPIO.BOTH}

		self.config = self.loadConfigFile()
				
		self.camera = None
		
		#
		# GPIO
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)

		GPIO.setup(self.config['hardware']['whiteLightPin'], GPIO.OUT)
		GPIO.output(self.config['hardware']['whiteLightPin'], 0)
		self.whiteIsOn = False

		GPIO.setup(self.config['hardware']['irLightPin'], GPIO.OUT)
		GPIO.output(self.config['hardware']['irLightPin'], 0)
		self.irIsOn = False
		
		if self.config['scope']['autoArm']:
			print('auto arm is on')
			self.state = "armed"
		else:
			self.state = "idle"

		if self.config['scope']['frameIn']['enabled']:
			pin = int(self.config['scope']['frameIn']['pin'])
			polarity = self.config['scope']['frameIn']['polarity']
			polarity = self.polarityDict_[polarity]
			GPIO.setup(pin, GPIO.IN)
			GPIO.add_event_detect(pin, polarity, callback=self.frame_Callback, bouncetime=200) # ms

		if self.config['scope']['triggerIn']['enabled']:
			pin = self.config['scope']['triggerIn']['pin']
			polarity = self.config['scope']['triggerIn']['polarity']
			polarity = self.polarityDict_[polarity]
			GPIO.setup(pin, GPIO.IN)
			GPIO.add_event_detect(pin, polarity, callback=self.triggerIn_Callback, bouncetime=200) # ms

		if self.config['scope']['triggerOut']['enabled']:
			pin = self.config['scope']['triggerOut']['pin']
			#polarity = self.config['scope']['triggerOut']['polarity']
			GPIO.setup(pin, GPIO.OUT)

		#
		self.trial = trial()
		'''
		self.trialNum = 0
		self.trial = OrderedDict()
		self.trial['startTimeSeconds'] = None
		'''
		
		#self.currentFile = 'None'
		#self.currentStartSeconds = float('nan')

		#
		# save path
		self.videoPath = self.config['video']['savepath']
		self.saveVideoPath = '' # set when we start video recording
		if not os.path.isdir(self.videoPath):
			os.makedirs(self.videoPath)
			
		#self.lastStillTime = '' # time.time()
		
		self.lastResponse = ''
		
		self.armVideoRunning = False
		
		#
		# temperature and humidity
		self.lastTemperatureTime = 0
		self.lastTemperature = None
		self.lastHumidity = None
		
		if g_dhtLoaded and self.config['hardware']['readtemperature']>0:
			#print('   Initialized DHT temperature sensor')
			logger.debug('Initialized DHT temperature sensor')
			GPIO.setup(self.config['hardware']['temperatureSensor'], GPIO.IN)
			myThread = threading.Thread(target = self.tempThread)
			myThread.daemon = True
			myThread.start()
		else:
			#print('   Did not find DHT temperature sensor')
			logger.debug('Did not find DHT temperature sensor')
			
		#
		# system information
		self.ip = self.whatismyip()
		self.gbRemaining = None
		self.gbSize = None
		self.cpuTemperature = None
		
		# get the raspberry pi version, we can run on version 2/3, on model B streaming does not work
		cmd = 'cat /proc/device-tree/model'
		child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
		out, err = child.communicate() # out is something like 'Raspberry Pi 2 Model B Rev 1.1'
		out = out.decode('utf-8')
		#print('   ', out)
		logger.info(out)
		self.raspberryModel = out
		
		# get the version of Raspian, we want to be running on Jessie or Stretch
		import platform
		dist = platform.dist() # 8 is jessie, 9 is stretch
		if len(dist)==3:
			if float(dist[1]) >= 8:
				#print('   Running on Jessie, Stretch or newer')
				logger.info('Running on Jessie, Stretch or newer')
			else:
				#print('   Warning: not designed to work on Raspbian before Jessie')
				logger.warning('Not designed to work on Raspbian before Jessie')
		
		#print('   Done initializing home.py')
		logger.debug('finished home.init()')
		
	'''
	def startTrial(self, now=time.time()):
		print('startTrial now:', now)
		# todo: make a trial file to log timing within a trial
		logger.debug('startTrial')
		timeStr = time.strftime('%Y%m%d_%H%M%S', time.localtime(now))
		self.trialNum += 1
		self.trial['startTimeSeconds'] = now
		self.trial['startTimeStr'] = timeStr #datetime.now().strftime('%Y%m%d_%H%M%S')
		self.trial['trialNum'] = self.trialNum
		self.trial['epochNum'] = 0 # increment each time we make a new file
		self.trial['frameNum'] = 0
		self.trial['frameTimes'] = [] # relative to self.trial['startTimeSeconds']
		self.trial['currentFile'] = 'None'
		self.trial['lastStillTime'] = None
		self.trial['timeRemaining'] = None 

		# todo: make trial a class and add its own log file (one per trial)
		self.log(self, 'startTrial', '', '', 1, now=now)
	'''
		
	'''
	def newEpoch(self):
		if self.trial['startTimeSeconds']:
			self.trial['epochNum'] += 1
	'''
			
	'''
	def stopTrial(self):
		# todo: finish up and close trial file
		logger.debug('stopTrial')
		self.trial['startTimeSeconds'] = None # critical, using this to see if trial is running
		self.trial['currentFile'] = 'None'
		try:
			#self.camera.annotate_background = picamera.Color('black')
			self.camera.annotate_text = ''
		except PiCameraClosed as e:
			print(e)
	'''
	
	def isState(self, thisState):
		''' Return True if self.state == thisState'''
		return True if self.state==thisState else False
		
	def frame_Callback(self, pin):
		now = time.time()
		if self.trial.isRunning:
			self.trial.newEvent('frame', self.trial.numFrames + 1, now=now)
			if self.camera:
				#todo: fix annotation background
				#todo: make sure we clear annotation background
				try:
					self.camera.annotate_background = picamera.Color('black')
					self.camera.annotate_text = ' ' + str(self.trial.numFrames) + ' ' 
				except PiCameraClosed as e:
					print(e)
			#self.log(self, 'newFrame', '', '', frameNumber, now=now)
			#logger.debug('frame_Callback finished')
			
	def triggerIn_Callback(self, pin):
		now = time.time()
		self.startArmVideo(now=now)
		#logger.debug("triggerIn_Callback finished trial:" + str(self.trial['frameNum']))
				
	def log(self, event1, event2, event3, state, now=time.time()):
		# log events to a file
		print('log now:', now)
		delimStr = ','
		eolStr = '\n'

		dateStr = time.strftime('%Y%m%d', time.localtime(now))
		timeStr = time.strftime('%H:%M:%S', time.localtime(now))
		logFile = dateStr + '.txt'
		logFolder = os.path.join(self.videoPath, dateStr)
		logPath = os.path.join(logFolder, logFile)
		if not os.path.isfile(logPath):
			if not os.path.exists(logFolder):
				os.makedirs(logFolder)
			with open(logPath,'a') as file:
				oneLine = 'date' + delimStr + 'time' + delimStr + 'seconds' + delimStr + 'event1' + delimStr + 'event2' + delimStr + 'event3' + delimStr + 'state' + eolStr
				file.write(oneLine)
		with open(logPath,'a') as file:
			oneLine = dateStr + delimStr + timeStr + delimStr + str(now) + delimStr + str(event1) + delimStr + str(event2) + delimStr + str(event3) + delimStr + str(state) + eolStr
			file.write(oneLine)
		
	def setParam(self, param, value):
		#print('setParam()', param, value, 'type:', type(value))
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
			
		#print('   was:', self.config[one][two], 'type:', type(self.config[one][two]))
		theType = type(self.config[one][two])
		if theType == str:
			value = str(value)
		if theType == int:
			value = int(value)
		if theType == bool:
			if value == 'false':
				value = False
			if value == 'true':
				value = True
			value = bool(value)
		# set
		self.config[one][two] = value
		
		self.lastResponse = one + ' ' + two + ' is now ' + str(value)
		
		#print('   now:', self.config[one][two], 'type:', type(self.config[one][two]))
		logger.debug('finished ' + str(self.config[one][two]))

	def loadConfigDefaultsFile(self):
		logger.debug('loadConfigDefaultsFile')
		with open('config_defaults.json') as configFile:
			self.config = json.load(configFile)
		self.lastResponse = 'Loaded default options file'
	
	def loadConfigFile(self):
		logger.debug('loadConfigFile')
		with open('config.json') as configFile:
			config = json.load(configFile, object_pairs_hook=OrderedDict)
		return config
	
	def saveConfigFile(self):
		logger.debug('saveConfigFile')
		with open('config.json', 'w') as outfile:
			json.dump(self.config, outfile, indent=4)
		self.lastResponse = 'Saved options file'
	
	def getStatus(self):
		# return the status of the server, all params
		# is called at a short interval, ~1 sec

		#logger.info('xxx testing info log from home.py')

		now = datetime.now()
				
		status = OrderedDict()

		status['server'] = OrderedDict()
		status['server']['state'] = self.state
		status['server']['lastResponse'] = self.lastResponse # filled in by each route

		status['lights'] = OrderedDict()
		status['lights']['irLED'] = self.irIsOn
		status['lights']['whiteLED'] = self.whiteIsOn

		status['trial'] = self.trial.trial

		# special case
		if self.trial.isRunning:
			status['trial']['epochTimeElapsed'] = self.trial.epochTimeElapsed
		else:
			status['trial']['epochTimeElapsed'] = None

		
		# temperature and humidity
		status['environment'] = OrderedDict()
		status['environment']['temperature'] = self.lastTemperature
		status['environment']['humidity'] = self.lastHumidity
			
		'''
		add a web button to refresh this
		self.drivespaceremaining()
		'''
		status['system'] = OrderedDict()
		status['system']['date'] = now.strftime('%Y-%m-%d')
		status['system']['time'] = now.strftime('%H:%M:%S')
		status['system']['ip'] = self.ip
		status['system']['hostname'] = socket.gethostname()
		status['system']['gbRemaining'] = self.gbRemaining
		status['system']['gbSize'] = self.gbSize
		status['system']['cpuTemperature'] = self.cpuTemperature

		return status

	def getConfig(self):
		# parameters that can be set by user
		return self.config
		
	def stop(self):
		logger.debug('stop')
		self.record(0)
		self.stream(0)
		self.stopArmVideo()
		self.trial.stopTrial()
		
	def record(self,onoff):
		'''
		start and stop video recording
		'''
		okGo = self.state in ['idle'] if onoff else self.state in ['recording']
		logger.debug('record onoff:' + str(onoff) + ' okGo:' + str(okGo))
		#print('record() got onoff:', onoff, 'okGo:', okGo)
		
		if not okGo:
			self.lastResponse = 'Recording not allowed while ' + self.state
		else:
			self.state = 'recording' if onoff else 'idle'
			if onoff:
				# set output path
				self.trial.startTrial()
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d')
				self.saveVideoPath = os.path.join(self.videoPath, startTimeStr)
				if not os.path.isdir(self.saveVideoPath):
					print('home.record() is making output directory:', self.saveVideoPath)
					os.makedirs(self.saveVideoPath)
								
				# start a background thread
				thread = threading.Thread(target=self.recordVideoThread, args=())
				thread.daemon = True							# Daemonize thread
				thread.start()									# Start the execution
			else:
				self.trial.stopTrial()
				#self.currentStartSeconds = float('nan')
				# this is set when the thread actually exits
				#self.currentFile = 'None'
				# turn off lights
				if self.config['lights']['auto']:
					self.whiteLED(False)
					self.irLED(False)

			self.lastResponse = 'Recording is ' + ('on' if onoff else 'off')
	
	def stream(self,onoff):
		'''
		start and stop video stream
		'''
		okGo = self.state in ['idle'] if onoff else self.state in ['streaming']
		logger.debug('stream onoff:' + str(onoff) + ' okGo:' + str(okGo))

		if not okGo:
			self.lastResponse = 'Streaming not allowed during ' + self.state
		else:
			self.state = 'streaming' if onoff else 'idle'
			#self.log('streaming', '', '', onoff)
			if onoff:
				width = self.config['stream']['resolution'].split(',')[0]
				height = self.config['stream']['resolution'].split(',')[1]
				'''
				cmd = './stream start ' \
					+ width \
					+ ' ' \
					+ height
				print('cmd:', cmd)
				child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
				out, err = child.communicate()
				print('stream() out:', out)
				print('stream() err:', err)
				'''
				cmd = ["./stream", "start", str(width), str(height)]
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
					self.lastResponse = 'Streaming is on'
				except subprocess.CalledProcessError as e:
				    print('e:', e)
				    print('e.returncode:', e.returncode) # 1 is failure, 0 is sucess
				    print('e.output:', e.output)
				    self.lastResponse = e.output
			else:
				'''
				cmd = './stream stop'
				print('cmd:', cmd)
				child = subprocess.Popen(cmd, shell=True)
				out, err = child.communicate()
				print('stream() out:', out)
				print('stream() err:', err)
				'''
				cmd = ["./stream", "stop"]
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
					self.lastResponse = 'Streaming is off'
				except subprocess.CalledProcessError as e:
				    print('e:', e)
				    print('e.returncode:', e.returncode) # 1 is failure, 0 is sucess
				    print('e.output:', e.output)
				    self.lastResponse = e.output
			

	def arm(self, onoff):
		'''
		start and stop arm
		'''
		okGo = self.state in ['idle'] if onoff else self.state in ['armed']
		logger.debug('arm onoff:' + str(onoff) + ' okGo:' + str(okGo))
		if not okGo:
			self.lastResponse = 'Arming not allowed during ' + self.state
		else:
			self.state = 'armed' if onoff else 'idle'
			#self.log('arm', '', '', onoff)
			if onoff:
				# spawn background task with video loop
				#try:
				if 1:
					#print('arm() initializing camera')
					logger.debug('Initializing camera')
					self.camera = picamera.PiCamera()
					width = int(self.config['video']['resolution'].split(',')[0])
					height = int(self.config['video']['resolution'].split(',')[1])
					self.camera.resolution = (width, height)
					self.camera.led = 0
					self.camera.framerate = self.config['video']['fps']
					self.camera.start_preview()

					#print('startArm() starting circular stream')
					logger.debug('Starting circular stream')
					self.circulario = picamera.PiCameraCircularIO(self.camera, seconds=self.config['scope']['bufferSeconds'])
					self.camera.start_recording(self.circulario, format='h264')				
				#except PiCameraMMALError:
				#	print 'startArm() error: PiCameraMMALError'
				#except:
				#	print('ERROR: startArm() error')
				#	return 0
			else:
				if self.camera:
					# stop background task with video loop
					self.camera.stop_recording()	
					self.camera.close()
			self.lastResponse = 'Armed is ' + ('on' if onoff else 'off')
	
	def startArmVideo(self, now=time.time()):
		if not self.isState('armed'):
			self.lastResponse = 'startArmVideo not allowed during ' + self.state
		else:
			self.state = 'armedrecording'
			self.trial.startTrial(now=now)
			# start a background thread
			thread = threading.Thread(target=self.armVideoThread, args=())
			thread.daemon = True							# Daemonize thread
			thread.start()									# Start the execution
			self.lastResponse = 'startArmVideo'
			
	def stopArmVideo(self):
		if not self.isState('armedrecording'):
			self.lastResponse = 'stopArmVideo not allowed during ' + self.state
		else:
			# force armVideoThread() out of while loop
			self.trial.stopTrial()
			self.state = 'armed'
			#self.currentFile = ''
			self.lastResponse = 'stopArmVideo'

	def irLED(self, onoff, allow=False):
		# pass allow=true to control light during recording
		if self.config['lights']['auto'] and not allow and self.isState('recording'):
			self.lastResponse = 'Not allowed during recording'
		else:
			GPIO.output(self.config['hardware']['irLightPin'], onoff)
			changed = self.irIsOn != onoff
			self.irIsOn = onoff
			if changed:
				#self.log('lights', 'ir', '', onoff)
				self.trial.newEvent('irLED', onoff, now=time.time()) 
			if not allow:
				self.lastResponse = 'ir light is ' + ('on' if onoff else 'off')

	def whiteLED(self,onoff, allow=False):
		# pass allow=true to control light during recording
		if self.config['lights']['auto'] and not allow and self.isState('recording'):
			self.lastResponse = 'Not allowed during recording'
		else:
			GPIO.output(self.config['hardware']['whiteLightPin'], onoff)
			changed = self.whiteIsOn != onoff
			self.whiteIsOn = onoff
			if changed:
				#self.log('lights', 'white', '', onoff)
				self.trial.newEvent('whiteLED', onoff, now=time.time()) 
			if not allow:
				self.lastResponse = 'white light is ' + ('on' if onoff else 'off')

	def controlLights(self):
		# control lights during recording
		if self.config['lights']['auto']:
			now = datetime.now()
			isDaytime = now.hour > self.config['lights']['sunrise'] and now.hour < self.config['lights']['sunset']
			if isDaytime:
				self.whiteLED(True, allow=True)
				self.irLED(False, allow=True)
			else:
				self.whiteLED(False, allow=True)
				self.irLED(True, allow=True)
			
	def recordVideoThread(self):
		# record individual video files in background thread
		with picamera.PiCamera() as camera:
			camera.led = False
			width = int(self.config['video']['resolution'].split(',')[0])
			height = int(self.config['video']['resolution'].split(',')[1])
			camera.resolution = (width, height)
			camera.framerate = self.config['video']['fps']

			stillPath = os.path.dirname(__file__) + '/static/' + 'still.jpg'
			
			lastStill = 0
			numberOfRepeats = self.config['video']['numberOfRepeats']
			currentRepeat = 1
			while self.isState('recording') and currentRepeat<=numberOfRepeats:
				now = time.time()
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d_%H%M%S')

				#the file we are about to record/save
				currentFile = startTimeStr + '.h264'
				
				# todo: fix logic here
				self.trial.trial['currentFile'] = currentFile
	
				# save into date folder
				dateStr = startTime.strftime('%Y%m%d')
				self.saveVideoPath = os.path.join(self.videoPath, dateStr)
				if not os.path.isdir(self.saveVideoPath):
					print('home.recordVideoThread() is making output directory:', self.saveVideoPath)
					os.makedirs(self.saveVideoPath)

				thisVideoFile = os.path.join(self.saveVideoPath, currentFile)

				self.trial.newEpoch(now)
				self.trial.newEvent('recordVideo', thisVideoFile, now=now)
				
				logger.debug('Start video file:' + currentFile)
	
				camera.start_recording(thisVideoFile)
				while self.isState('recording') and (time.time() < (now + self.config['video']['fileDuration'])):
					self.controlLights()
					camera.wait_recording(0.3)
					self.lastResponse = 'Recording file: ' + currentFile
					if self.config['video']['captureStill'] and time.time() > (lastStill + self.config['video']['stillInterval']):
						camera.capture(stillPath, use_video_port=True)
						lastStill = time.time()
						'''
						self.trial['lastStillTime'] = datetime.now().strftime('%Y%m%d %H:%M:%S')
						'''
				camera.stop_recording()
				currentRepeat += 1
				#self.log('video', thisVideoFile, currentFile, False)
				logging.debug('recordVideoThread fell out of inner while')

				# convert to mp4
				if self.config['video']['converttomp4']:
					self.lastResponse = 'Converting to mp4'
					self.convertVideo(thisVideoFile, self.config['video']['fps'])
					self.lastResponse = ''
				self.drivespaceremaining()
			print('yyy', currentRepeat,numberOfRepeats, self.state)
			self.state = 'idle'
			self.trial.stopTrial()
			logging.debug('recordVideoThread fell out of outer while')

	def armVideoThread(self):
		'''
		Start recording from circular stream in response to trigger.
		This will record until (i) fileDuration or (ii) stop trigger
		'''
		if self.camera:
			#self.camera.annotate_text = 'S'
			#self.camera.annotate_background = picamera.Color('black')
			lastStill = 0
			stillPath = os.path.dirname(__file__) + '/static/' + 'still.jpg'
			numberOfRepeats = self.config['video']['numberOfRepeats']
			currentRepeat = 1
			while self.isState('armedrecording') and currentRepeat<=numberOfRepeats:
				#todo: log time when trigger in is received
				now = time.time()
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d_%H%M%S')
				beforefilename = startTimeStr + '_before' + '.h264'
				afterfilename = startTimeStr + '_after' + '.h264'

				# save into date folder
				startTimeStr = startTime.strftime('%Y%m%d')
				self.saveVideoPath = os.path.join(self.videoPath, startTimeStr)
				if not os.path.isdir(self.saveVideoPath):
					print('home.armVideoThread() is making output directory:', self.saveVideoPath)
					os.makedirs(self.saveVideoPath)

				beforefilepath = os.path.join(self.saveVideoPath, beforefilename)
				afterfilepath = os.path.join(self.saveVideoPath, afterfilename)
				# record the frames "after" motion
				try:
					self.camera.split_recording(afterfilepath)
				except picamera.exc.PiCameraNotRecording:
					print('xxx000xxx CAUGHT IT')
				
				# todo: fix logic here
				self.trial.trial['currentFile'] = afterfilename

				self.trial.newEpoch(now)
				self.trial.newEvent('recordArmVideo', afterfilepath, now=now)

				# Write the 10 seconds "before" motion to disk as well
				self.write_video_(self.circulario, beforefilepath)

				fileDuration = self.config['video']['fileDuration']
				stopOnTrigger = 0
				while self.isState('armedrecording') and not stopOnTrigger and (time.time()<(now + fileDuration)):
					#todo: i need to clean up logic of start/stop armed recording
					self.camera.wait_recording(1) # seconds
					
					'''
					#this is for single trigger/frame pin in ScanImage
					if not useTwoTriggerPins and (time.time() > (self.lastFrameTime + self.lastFrameTimeout)):
						print 'run() is stopping after last frame timeout'
						stopOnTrigger = 1
					'''
					
					if self.config['video']['captureStill'] and time.time() > (lastStill + self.config['video']['stillInterval']):
						#print('armVideoThread capturing still:', stillPath)
						self.camera.capture(stillPath, use_video_port=True)
						lastStill = time.time()
						'''
						self.trial['lastStillTime'] = datetime.now().strftime('%Y%m%d %H:%M:%S')
						'''
						
				#print('startVideoArm() received stopOnTrigger OR self.videoStarted==0 OR past fileDuration')
				logger.debug('armVideoThread fell out of inner while loop, state:' + self.state)
				self.camera.split_recording(self.circulario)
				currentRepeat += 1
				
				# convert to mp4
				if self.config['video']['converttomp4']:
					# before
					self.lastResponse = 'Converting to mp4'
					self.convertVideo(beforefilepath, self.config['video']['fps'])
					# after
					self.lastResponse = 'Converting to mp4'
					self.convertVideo(afterfilepath, self.config['video']['fps'])

					self.lastResponse = ''

				self.drivespaceremaining()
									
				time.sleep(0.005) # seconds
			print('yyy', currentRepeat,numberOfRepeats, self.state)
			logger.debug('startVideoArm fell out of outer while loop')
			self.state = 'armed'
			self.trial.stopTrial()
			#self.camera.stop_recording()	
			#self.camera.close()
		time.sleep(0.05)

	def tempThread(self):
		# thread to run temperature/humidity in background
		# dht is blocking, long delay cause delays in web interface
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
							# todo: log this to a file
						# set even on fail, this way we do not immediately hit it again
						self.lastTemperatureTime = time.time()
					except:
						print('readTemperature() exception reading temperature/humidity')
			time.sleep(0.5)
	
	#called from armVideoThread()
	def write_video_(self, stream, beforeFilePath):
		# Write the entire content of the circular buffer to disk. No need to
		# lock the stream here as we're definitely not writing to it simultaneously
		with io.open(beforeFilePath, 'wb') as output:
			for frame in stream.frames:
				if frame.frame_type == picamera.PiVideoFrameType.sps_header:
					stream.seek(frame.position)
					break
			while True:
				buf = stream.read1()
				if not buf:
					break
				output.write(buf)
		# Wipe the circular stream once we're done
		stream.seek(0)
		stream.truncate()

	def convertVideo(self, videoFilePath, fps):
		# at end of video recording, convert h264 to mp4
		# also build a db.txt with videos in a folder
		logger.debug('converting video:' + videoFilePath + ' fps:' + str(fps))
		'''
		cmd = './convert_video.sh ' + videoFilePath + ' ' + str(fps)
		child = subprocess.Popen(cmd, shell=True)
		out, err = child.communicate()
		print('   convertVideo() out:', out)
		print('   convertVideo() err:', err)
		'''
		
		cmd = ["./convert_video.sh", videoFilePath, str(fps)]
		try:
			out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
			self.lastResponse = 'Converted video to mp4'
		except subprocess.CalledProcessError as e:
			print('e:', e)
			print('e.returncode:', e.returncode) # 1 is failure, 0 is sucess
			print('e.output:', e.output)
			self.lastResponse = e.output
		
		# append to dict and save in file
		dirname = os.path.dirname(videoFilePath) 
		mp4File = os.path.basename(videoFilePath).split('.')[0] + '.mp4'
		mp4Path = os.path.join(dirname, mp4File)
		#print('mp4Path:', mp4Path)
		#todo: also include .h264 (if we are not converting to .mp4)
		command = "avprobe -show_format -show_streams -loglevel 'quiet' " + str(mp4Path) + ' -of json'
		#command = "avprobe -show_format -show_streams " + str(mp4Path) + ' -of json'
		#print(command)
		child = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
		data, err = child.communicate()
		data = data.decode('utf-8') # python 3
		data = json.loads((data))
		#print data
		fd = {}
		fd['path'] = mp4Path
		fd['file'] = mp4File
		if 'format' in data:
			fd['duration'] =  math.floor(float(data['format']['duration'])*100)/100
		else:
			fd['duration'] =  '?'
		if 'streams' in data:
			fd['width'] =  data['streams'][0]['width']
			fd['height'] =  data['streams'][0]['height']
			#stretch
			#fd['fps'] = data['streams'][0]['avg_frame_rate'].split('/')[0] # parsing 25/1
			#jessie
			#fd['fps'] = data['streams'][0]['r_frame_rate'].split('/')[0] # parsing 25/1
			fd['fps'] = fps
		else:
			fd['width'] =  '?'
			fd['height'] =  '?'
			fd['fps'] = '?'
		
		# load existing database (list of dict)
		folder = os.path.dirname(videoFilePath)
		dbFile = os.path.join(folder,'db.txt')
		#print('dbFile:', dbFile)
		db = []
		if os.path.isfile(dbFile):
			db = json.load(open(dbFile))
			#print 'loaded db:', db
		# append
		db.append(fd)
		# save
		txt = json.dumps(db)
		f = open(dbFile,"w")
		f.write(txt)
		f.close()
					
	#
	# Utility
	#
	'''
	def whatismyip(self):
		arg='ip route list'
		p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
		data = p.communicate()[0].decode('utf-8').strip()
		ipaddr = data[data.index('src')+1]
		return ipaddr
	'''
	
	def whatismyip(self):
		ips = subprocess.check_output(['hostname', '--all-ip-addresses'])
		ips = ips.decode('utf-8').strip()
		return ips

	def drivespaceremaining(self):
		#see: http://stackoverflow.com/questions/51658/cross-platform-space-remaining-on-volume-using-python
		statvfs = os.statvfs('/home/pi/video')
		
		#http://www.stealthcopter.com/blog/2009/09/python-diskspace/
		capacity = statvfs.f_bsize * statvfs.f_blocks
		available = statvfs.f_bsize * statvfs.f_bavail
		used = statvfs.f_bsize * (statvfs.f_blocks - statvfs.f_bavail) 
		#print 'drivespaceremaining()', used/1.073741824e9, available/1.073741824e9, capacity/1.073741824e9
		self.gbRemaining = available/1.073741824e9
		self.gbSize = capacity/1.073741824e9

		#round to 2 decimal places
		self.gbRemaining = "{0:.2f}".format(self.gbRemaining)
		self.gbSize = "{0:.2f}".format(self.gbSize)
		#print self.gbRemaining, self.gbSize

		#cpu temperature
		res = os.popen('vcgencmd measure_temp').readline()
		self.cpuTemperature = res.replace("temp=","").replace("'C\n","")
		#print 'cpu temp = ', self.cpuTemperature

	# generate a file list of video files
	def make_tree(self, path):
		filelist = []
		for root, dirs, files in os.walk(path):
			for file in files:
				if file.endswith('.h264'):
					filelist.append(file)
		return filelist


