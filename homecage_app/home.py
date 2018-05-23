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

#log = logging.getLogger('homecage_app.home')
#log.info('testing info log from home.py')
logger = logging.getLogger('homecage.home')

# load dht temperature/humidity sensor library
g_dhtLoaded = 0
try:
	import Adafruit_DHT 
	g_dhtLoaded = 1
except:
	g_dhtLoaded = 0
	print('WARNING: home.py did not load Adafruit_DHT')

class home:
	def __init__(self):
		self.init()

	def init(self):
		print('Initializing home.py')
		logger.debug('start init')
		
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
		self.trialNum = 0
		self.trial = OrderedDict()
		self.trial['startTimeSeconds'] = None
		
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
			print('   Initialized DHT temperature sensor')
			GPIO.setup(self.config['hardware']['temperatureSensor'], GPIO.IN)
			myThread = threading.Thread(target = self.tempThread)
			myThread.daemon = True
			myThread.start()
		else:
			print('   Did not find DHT temperature sensor')
			
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
		print('   ', out)
		self.raspberryModel = out
		
		# get the version of Raspian, we want to be running on Jessie or Stretch
		import platform
		dist = platform.dist() # 8 is jessie, 9 is stretch
		if len(dist)==3:
			if float(dist[1]) >= 8:
				print('   Running on Jessie, Stretch or newer')
			else:
				print('   Warning: not designed to work on Raspbian before Jessie')
		
		print('   Done initializing home.py')
		logger.debug('finish init')
		
	def startTrial(self):
		# todo: make a trial file to log timing within a trial
		startTime = datetime.now()
		self.trialNum += 1
		self.trial['startTimeSeconds'] = time.time()
		self.trial['timeStamp'] = datetime.now().strftime('%Y%m%d_%H%M%S')
		self.trial['trialNum'] = self.trialNum
		self.trial['epochNum'] = 0 # increment each time we make a new file
		self.trial['frameNum'] = 0
		self.trial['lastFrameTime'] = None
		self.trial['frameTimes'] = []
		self.trial['currentFile'] = 'None'
		self.trial['lastStillTime'] = None
		self.trial['timeRemaining'] = None 

		dateStr = startTime.strftime('%Y%m%d')
		timeStr = startTime.strftime('%H%M%S')
		
	def newEpoch(self):
		if self.trial['startTimeSeconds']:
			self.trial['epochNum'] += 1
			
	def stopTrial(self):
		# todo: finish up and close trial file
		print('stopTrial()')
		self.trial['startTimeSeconds'] = None # critical, using this to see if trial is running
		self.trial['currentFile'] = 'None'

	def isState(self, thisState):
		''' Return True if self.state == thisState'''
		return True if self.state==thisState else False
		
	def frame_Callback(self, pin):
		print('framePin_Callback')
		now = time.time()
		if self.trial['startTimeSeconds'] is not None:
			#todo: append time relative to self.trial['startTimeSeconds']
			self.trial['frameNum'] += 1
			self.trial['lastFrameTime'] = now
			self.trial['frameTimes'].append(now)
			if self.camera:
				#todo: fix annotation background
				#todo: make sure we clear annotation background
				try:
					self.camera.annotate_background = picamera.Color('black')
					self.camera.annotate_text = ' ' + str(self.trial['frameNum']) + ' ' 
				except PiCameraClosed as e:
					print(e)
			print('framePin_Callback()', now, self.trial['frameNum'])
			
	def triggerIn_Callback(self, pin):
		print('triggerIn_Callback')
		self.startArmVideo()
				
	def log(self, event1, event2, event3, state):
		# log events to a file
		delimStr = ','
		eolStr = '\n'

		epochSeconds = time.time()
		startTime = datetime.now()
		dateStr = startTime.strftime('%Y%m%d')
		timeStr = startTime.strftime('%H%M%S')
		logFile = startTime.strftime('%Y%m%d') + '.txt'
		logFolder = os.path.join(self.videoPath, dateStr)
		logPath = os.path.join(logFolder, logFile)
		if not os.path.isfile(logPath):
			if not os.path.exists(logFolder):
				os.makedirs(logFolder)
			with open(logPath,'a') as file:
				oneLine = 'date' + delimStr + 'time' + delimStr + 'seconds' + delimStr + 'event1' + delimStr + 'event2' + delimStr + 'event3' + delimStr + 'state' + eolStr
				file.write(oneLine)
		with open(logPath,'a') as file:
			oneLine = dateStr + delimStr + timeStr + delimStr + str(epochSeconds) + delimStr + str(event1) + delimStr + str(event2) + delimStr + str(event3) + delimStr + str(state) + eolStr
			file.write(oneLine)
		
	def setParam(self, param, value):
		print('setParam()', param, value, 'type:', type(value))
		one, two = param.split('.')
		if one not in self.config:
			# error
			print('ERROR: setParam() did not find', one, 'in self.config')
			return
		if two not in self.config[one]:
			# error
			print('ERROR: setParam() did not find', two, 'in self.config["', one, '"]')
			return
			
		print('   was:', self.config[one][two], 'type:', type(self.config[one][two]))
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
		
		print('   now:', self.config[one][two], 'type:', type(self.config[one][two]))
		
	def loadConfigDefaultsFile(self):
		print('home.py loadConfigDefaultsFile()')
		with open('config_defaults.json') as configFile:
			self.config = json.load(configFile)
		self.lastResponse = 'Loaded default options file'
	
	def loadConfigFile(self):
		with open('config.json') as configFile:
			config = json.load(configFile, object_pairs_hook=OrderedDict)
		return config
	
	def saveConfigFile(self):
		print('home.py saveConfigFile()')
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

		# update trial (not used by home.py)
		if self.trial['startTimeSeconds']:
			self.trial['timeRemaining'] = round(self.config['video']['fileDuration'] - (time.time() - self.trial['startTimeSeconds']),2)
		else:
			self.trial['timeRemaining'] = None

		status['trial'] = self.trial
		
		# temperature and humidity
		status['environment'] = OrderedDict()
		status['environment']['temperature'] = self.lastTemperature
		status['environment']['humidity'] = self.lastHumidity
			
		self.drivespaceremaining()
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
		self.record(0)
		self.stream(0)
		self.stopArmVideo()
		self.stopTrial()
		
	def record(self,onoff):
		'''
		start and stop video recording
		'''
		okGo = self.state in ['idle'] if onoff else self.state in ['recording']
		print('record() got onoff:', onoff, 'okGo:', okGo)
		
		if not okGo:
			self.lastResponse = 'Recording not allowed while ' + self.state
		else:
			self.state = 'recording' if onoff else 'idle'
			if onoff:
				# set output path
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
				self.stopTrial()
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
		print('stream() got onoff:', onoff, 'okGo:', okGo)

		if not okGo:
			self.lastResponse = 'Streaming not allowed during ' + self.state
		else:
			self.state = 'streaming' if onoff else 'idle'
			self.log('streaming', '', '', onoff)
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
		print('arm() got onoff:', onoff, 'okGo:', okGo)
		if not okGo:
			self.lastResponse = 'Arming not allowed during ' + self.state
		else:
			self.state = 'armed' if onoff else 'idle'
			self.log('arm', '', '', onoff)
			if onoff:
				# spawn background task with video loop
				#try:
				if 1:
					print('arm() initializing camera')
					self.camera = picamera.PiCamera()
					width = int(self.config['video']['resolution'].split(',')[0])
					height = int(self.config['video']['resolution'].split(',')[1])
					self.camera.resolution = (width, height)
					self.camera.led = 0
					self.camera.framerate = self.config['video']['fps']
					self.camera.start_preview()

					print('startArm() starting circular stream')
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
	
	def startArmVideo(self):
		if not self.isState('armed'):
			self.lastResponse = 'startArmVideo not allowed during ' + self.state
		else:
			self.state = 'armedrecording'
			self.startTrial()
			# start a background thread
			thread = threading.Thread(target=self.armVideoTread, args=())
			thread.daemon = True							# Daemonize thread
			thread.start()									# Start the execution
			self.lastResponse = 'startArmVideo'
			
	def stopArmVideo(self):
		if not self.isState('armedrecording'):
			self.lastResponse = 'stopArmVideo not allowed during ' + self.state
		else:
			# force armVideoTread() out of while loop
			self.stopTrial()
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
				self.log('lights', 'ir', '', onoff)
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
				self.log('lights', 'white', '', onoff)
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
			while self.isState('recording') and currentRepeat <= numberOfRepeats:
				startNow = time.time()
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d_%H%M%S')

				#the file we are about to record/save
				currentFile = startTimeStr + '.h264'
				self.trial['currentFile'] = currentFile
				#self.currentStartSeconds = time.time()
				thisVideoFile = self.saveVideoPath + currentFile
	
				print('   Start video file:', currentFile)
				self.log('video', thisVideoFile, currentFile, True)
	
				camera.start_recording(thisVideoFile)
				while self.isState('recording') and (time.time() < (startNow + self.config['video']['fileDuration'])):
					self.controlLights()
					camera.wait_recording(0.3)
					self.lastResponse = 'Recording file: ' + currentFile
					if self.config['video']['captureStill'] and time.time() > (lastStill + self.config['video']['stillInterval']):
						print('   capturing still:', stillPath)
						camera.capture(stillPath, use_video_port=True)
						lastStill = time.time()
						self.trial['lastStillTime'] = datetime.now().strftime('%Y%m%d %H:%M:%S')
				camera.stop_recording()
				currentRepeat += 1
				self.log('video', thisVideoFile, currentFile, False)
				print('   Stop video file:', thisVideoFile)

				# convert to mp4
				if self.config['video']['converttomp4']:
					print('   Converting to .mp4', thisVideoFile)
					self.lastResponse = 'Converting to mp4'
					self.convertVideo(thisVideoFile, self.config['video']['fps'])
					self.lastResponse = ''
			self.state = 'idle'
			print('recordVideoThread() out of while')

	def armVideoTread(self):
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
				#try:
				if 1:
					#todo: log time when trigger in is received
					startTime0 = time.time()
					startTime = datetime.now()
					startTimeStr = startTime.strftime('%Y%m%d_%H%M%S')
					beforefilename = startTimeStr + '_before' + '.h264'
					afterfilename = startTimeStr + '_after' + '.h264'

					# save into date folder
					startTimeStr = startTime.strftime('%Y%m%d')
					self.saveVideoPath = os.path.join(self.videoPath, startTimeStr)
					if not os.path.isdir(self.saveVideoPath):
						print('home.armVideoTread() is making output directory:', self.saveVideoPath)
						os.makedirs(self.saveVideoPath)

					beforefilepath = os.path.join(self.saveVideoPath, beforefilename)
					afterfilepath = os.path.join(self.saveVideoPath, afterfilename)
					# record the frames "after" motion
					self.camera.split_recording(afterfilepath)
					self.trial['currentFile'] = afterfilename
					# Write the 10 seconds "before" motion to disk as well
					self.write_video_(self.circulario, beforefilepath)
	
					fileDuration = self.config['video']['fileDuration']
					stopOnTrigger = 0
					while self.isState('armedrecording') and not stopOnTrigger and (time.time()<(startTime0 + fileDuration)):
						self.camera.wait_recording(1) # seconds
						'''
						#this is for single trigger/frame pin in ScanImage
						if not useTwoTriggerPins and (time.time() > (self.lastFrameTime + self.lastFrameTimeout)):
							print 'run() is stopping after last frame timeout'
							stopOnTrigger = 1
						'''
						if self.config['video']['captureStill'] and time.time() > (lastStill + self.config['video']['stillInterval']):
							print('armVideoTread capturing still:', stillPath)
							self.camera.capture(stillPath, use_video_port=True)
							lastStill = time.time()
							self.trial['lastStillTime'] = datetime.now().strftime('%Y%m%d %H:%M:%S')
						
					print('startVideoArm() received stopOnTrigger OR self.videoStarted==0 OR past fileDuration')
					self.camera.split_recording(self.circulario)
					currentRepeat += 1
					
					# convert to mp4
					if self.config['video']['converttomp4']:
						# before
						print('   Converting to .mp4', beforefilepath)
						self.lastResponse = 'Converting to mp4'
						self.convertVideo(beforefilepath, self.config['video']['fps'])
						# after
						print('   Converting to .mp4', afterfilepath)
						self.lastResponse = 'Converting to mp4'
						self.convertVideo(afterfilepath, self.config['video']['fps'])

						self.lastResponse = ''
										
					time.sleep(0.005) # seconds
				#except:
				#	print('startVideoArm() except clause -->>ERROR')
			print('startVideoArm() fell out of while(self.state == armed) loop')
			self.state = 'armed'
			self.camera.stop_recording()	
			self.camera.close()
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
	
	#called from armVideoTread()
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
		print('=== convertVideo()', videoFilePath, fps)
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
		print(command)
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
		print('dbFile:', dbFile)
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


