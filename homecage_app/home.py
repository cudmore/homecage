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
	def __init__(self):
		self.init()

	def init(self):
		logger.debug('start home.init()')
		
		# dict to convert polarity string to number, e.g. self.polarity['rising'] yields GPIO.RISING
		self.polarityDict_ = { 'rising': GPIO.RISING, 'falling': GPIO.FALLING, 'both': GPIO.BOTH}

		self.config = self.loadConfigFile()
				
		self.trial = bTrial()
		self.camera = bCamera(self.trial)
		
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
		self.systemInfo = bUtil.getSystemInfo()
		
	def isState(self, thisState):
		''' Return True if self.state == thisState'''
		#return True if self.state==thisState else False
		return True if self.camera.state==thisState else False
		
	def frame_Callback(self, pin):
		now = time.time()
		if self.trial.isRunning:
			self.trial.newEvent('frame', self.trial.numFrames + 1, now=now)
			#todo: call self.camera.annotate()
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
		self.camera.startArmVideo(now=now)
		#logger.debug("triggerIn_Callback finished trial:" + str(self.trial['frameNum']))
				
	def setParam(self, param, value):
		#todo: pass camera values and set in self.camera
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

		now = datetime.now()
				
		status = OrderedDict()

		status['server'] = OrderedDict()
		status['server']['state'] = self.camera.state
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
			
		# system status (ip, host, cpu temperature, drive space remaining, etc)
		#todo: add a web button to refresh this self.drivespaceremaining()		'''
		status['system'] = OrderedDict()
		status['system']['date'] = now.strftime('%Y-%m-%d')
		status['system']['time'] = now.strftime('%H:%M:%S')
		for k, v in self.systemInfo.iteritems():
			status['system'][k] = v

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
		
	def record(self, onoff):
		self.camera.record(onoff)
		
	def stream(self, onoff):
		self.camera.stream(onoff)
		
	def arm(self, onoff):
		self.camera.arm(onoff)
	
	def startArmVideo(self, now=time.time()):
		self.camera.startArmVideo(now=now)
		
	def stopArmVideo(self):
		self.camera.stopArmVideo()
		
	
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
			
	def lightsThread(self):
		while self.isState('recording'):
			self.controlLights()
			time.sleep(0.5)
				
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
	
	"""
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
	"""
				
	# generate a file list of video files
	def make_tree(self, path):
		filelist = []
		for root, dirs, files in os.walk(path):
			for file in files:
				if file.endswith('.h264'):
					filelist.append(file)
		return filelist


