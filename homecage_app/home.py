# Robert Cudore
# 20171103

import os, time, math
import subprocess
import threading
from datetime import datetime
import collections
import json
import socket # to get hostname

import RPi.GPIO as GPIO
import picamera

# load dht temperature/humidity sensor library
g_dhtLoaded = 0
try:
	import Adafruit_DHT 
	g_dhtLoaded = 1
except:
	g_dhtLoaded = 0
	print 'error loading Adafruit_DHT, temperature and humidity will not work' 

class home:
	def __init__(self):
		self.init()

	def init(self):
		self.config = self.loadConfigFile()
		
		GPIO.setmode(GPIO.BCM)

		#lights
		#self.irLightPin = 7
		#self.whiteLightPin = 8

		GPIO.setwarnings(False)

		GPIO.setup(self.config['hardware']['whiteLightPin'], GPIO.OUT)
		GPIO.setup(self.config['hardware']['irLightPin'], GPIO.OUT)

		GPIO.output(self.config['hardware']['whiteLightPin'], 0)
		GPIO.output(self.config['hardware']['irLightPin'], 0)

		#if self.config['hardware']['temperatureSensor'] > 0:
		#	GPIO.setup(self.config['hardware']['temperatureSensor'], GPIO.IN)
		
		self.whiteIsOn = 0
		self.irIsOn = 0

		self.isRecording = False
		self.isStreaming = False
		
		#self.fps = 30
		#self.resolution = (self.config['video']['resolution'][0], self.config['video']['resolution'][1])
		#self.fileDuration = 5 #5*60
		#self.stillInterval = 2 # sec
		
		#self.lightsOnTime = 6
		#self.lightsOffTime = 18
		
		self.currentFile = 'None'
		self.currentStartSeconds = float('nan')
		self.videoPath = '/home/pi/video/'
		self.saveVideoPath = '' # set when we start video recording
		
		self.ip = self.whatismyip()
		self.lastResponse = ''
		
		self.streamWidth = 1024
		self.streamHeight = 768

		# temperature and humidity
		self.lastTemperatureTime = 0
		self.lastTemperature = None
		self.lastHumidity = None
		
		if g_dhtLoaded and self.config['hardware']['temperatureSensor'] > 0:
			myThread = threading.Thread(target = self.tempThread)
			myThread.daemon = True
			myThread.start()

		if not os.path.isdir('/home/pi/video'):
			os.makedirs('/home/pi/video')
		#if not os.path.isdir('/home/pi/video/mp4'):
		#	os.makedirs('/home/pi/video/mp4')
			
	# thread to run temperature/humidity in backfround
	# dht is blocking, long delay cause delays in web interface
	def tempThread(self):
		temperatureInterval = self.config['hardware']['temperatureInterval']
		pin = self.config['hardware']['temperatureSensor']
		while True:
			if g_dhtLoaded:
				if time.time() > self.lastTemperatureTime + temperatureInterval:
					try:
						humidity, temperature = Adafruit_DHT.read(Adafruit_DHT.DHT22, pin)
						if humidity is not None and temperature is not None:
							self.lastTemperature = math.floor(temperature * 100) / 100
							self.lastHumidity = math.floor(humidity * 100) / 100
							#print 'tempThread()', self.lastTemperature, self.lastHumidity
						# set even on fail, this way we do not immediately hit it again
						self.lastTemperatureTime = time.time()
					except:
						print 'readTemperature() exception reading temperature/humidity'
			time.sleep(0.5)
	
	def setParam(self, param, value):
		print 'setParam()', param, value
		one, two = param.split('.')
		print 'was:', self.config[one][two]
		self.config[one][two] = value
		
	def loadConfigDefaultsFile(self):
		print 'home.py loadConfigDefaultsFile()'
		with open('config_defaults.json') as configFile:
			self.config = json.load(configFile)
		self.lastResponse = 'Loaded default config file'
	
	def loadConfigFile(self):
		with open('config.json') as configFile:
			config = json.load(configFile)
		return config
	
	def saveConfigFile(self):
		print 'home.py saveConfigFile()'
		with open('config.json', 'w') as outfile:
			json.dump(self.config, outfile, indent=4)
		self.lastResponse = 'Saved config file'
	
	def getStatus(self):
		# return the status of the server, all params
		# is called at a short interval, ~1 sec

		now = datetime.now()
		microsecondStr = str(now.microsecond)[0:2]
				
		status = collections.OrderedDict()
		status['config'] = self.config

		status['date'] = now.strftime('%Y-%m-%d')
		status['time'] = now.strftime('%H:%M:%S.') + microsecondStr
		status['ip'] = self.ip
		status['hostname'] = socket.gethostname()

		status['isRecording'] = self.isRecording
		status['isStreaming'] = self.isStreaming
		status['irLED'] = self.irIsOn
		status['whiteLED'] = self.whiteIsOn

		#status['fps'] = self.config['video']['fps']
		#status['resolution'] = (self.config['video']['resolution'][0],self.config['video']['resolution'][1])
		#status['fileDuration'] = self.fileDuration
		status['currentFile'] = self.currentFile
		if self.isRecording and self.currentStartSeconds>0:
			status['timeRemaining'] = math.trunc(self.config['video']['fileDuration'] - (time.time() - self.currentStartSeconds))
		else:
			status['timeRemaining'] = 'n/a'
			
		#status['stillInterval'] = self.config['video']['stillInterval']
		status['lastResponse'] = self.lastResponse # filled in by each route

		#status['streamWidth'] = self.streamWidth
		#status['streamHeight'] = self.streamHeight
		
		filelist = self.make_tree('/home/pi/video')
		status['videofilelist'] = json.dumps(filelist)
		
		# temperature and humidity
		status['temperature'] = self.lastTemperature
		status['humidity'] = self.lastHumidity
			
		status['controlLights'] = self.config['lights']['controlLights']
		
		#print "status['videofilelist']:", status['videofilelist']
		
		return status

	def getParams(self):
		# parameters that can be set by user
		return self.config
		
	def record(self,onoff):
		if self.isStreaming:
			self.lastResponse = 'Recording not allowed during streaming'
		else:
			self.isRecording = onoff
			if self.isRecording:
				# set output path
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d')
				self.saveVideoPath = self.videoPath + startTimeStr + '/'
				print 'home.record() is making output directory:', self.saveVideoPath
				if not os.path.isdir(self.saveVideoPath):
					os.makedirs(self.saveVideoPath)
				#mp4Path = self.saveVideoPath + 'mp4'
				#if not os.path.isdir(mp4Path):
				#	os.makedirs(mp4Path)
								
				#self.currentStartSeconds = time.time()
				#self.currentFile = datetime.now().strftime('%Y%m%d_%H%M%S')
				# start a background thread
				thread = threading.Thread(target=self.recordVideoThread, args=())
				thread.daemon = True							# Daemonize thread
				thread.start()									# Start the execution
			else:
				self.currentStartSeconds = float('nan')
				self.currentFile = 'None'
				# turn off lights
				self.whiteLED(0)
				self.irLED(0)

			self.lastResponse = 'Recording is ' + ('on' if onoff else 'off')
	
	def convertVideo(self, videoFilePath, fps):
		print 'convertVideo()', videoFilePath, fps
		cmd = './convert_video.sh ' + videoFilePath + ' ' + str(fps)
		child = subprocess.Popen(cmd, shell=True)
		out, err = child.communicate()
		#print 'out:', out
		#print 'err:', err
		
	def stream(self,onoff):
		print 'stream()'
		if self.isRecording:
			self.lastResponse = 'Streaming not allowed during recording'
		else:
			self.isStreaming = onoff
			if self.isStreaming:
				cmd = './stream start ' \
					+ str(self.config['stream']['streamResolution'][0]) \
					+ ' ' \
					+ str(self.config['stream']['streamResolution'][1])
				print 'cmd:', cmd
				child = subprocess.Popen(cmd, shell=True)
				out, err = child.communicate()
				#print 'out:', out
				#print 'err:', err
			else:
				cmd = './stream stop'
				print 'cmd:', cmd
				child = subprocess.Popen(cmd, shell=True)
				out, err = child.communicate()
				#print 'out:', out
				#print 'err:', err
			self.lastResponse = 'Streaming is ' + ('on' if self.isStreaming else 'off')

	def irLED(self, onoff, allow=False):
		# pass allow=true to control light during recording
		if self.config['lights']['controlLights'] and not allow and self.isRecording:
			self.lastResponse = 'Not allowed during recording'
		else:
			GPIO.output(self.config['hardware']['irLightPin'], onoff)
			self.irIsOn = onoff
			if not allow:
				self.lastResponse = 'ir LED is ' + ('on' if onoff else 'off')

	def whiteLED(self,onoff, allow=False):
		# pass allow=true to control light during recording
		if not allow and self.isRecording:
			self.lastResponse = 'Not allowed during recording'
		else:
			GPIO.output(self.config['hardware']['whiteLightPin'], onoff)
			self.whiteIsOn = onoff
			if not allow:
				self.lastResponse = 'white LED is ' + ('on' if onoff else 'off')

	def controlLights(self):
		# control lights during recording
		if self.config['lights']['controlLights']:
			now = datetime.now()
			isDaytime = now.hour > self.config['lights']['sunrise'] and now.hour < self.config['lights']['sunset']
			if isDaytime:
				self.whiteLED(1, allow=True)
				self.irLED(0, allow=True)
			else:
				self.whiteLED(0, allow=True)
				self.irLED(1, allow=True)
			
	def recordVideoThread(self):
		# record individual video files in background thread
		with picamera.PiCamera() as camera:
			camera.led = False
			camera.resolution = (self.config['video']['resolution'][0], self.config['video']['resolution'][1])
			camera.framerate = self.config['video']['fps']

			stillPath = os.path.dirname(__file__) + '/static/' + 'still.jpg'
			
			lastStill = 0
			while self.isRecording:
				startNow = time.time()
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d_%H%M%S')

				#the file we are about to record/save
				self.currentFile = startTimeStr + '.h264'
				self.currentStartSeconds = time.time()
				thisVideoFile = self.saveVideoPath + self.currentFile
	
				print '	 Start video file:', self.currentFile
	
				camera.start_recording(thisVideoFile)
				#camera.wait_recording(self.config['video']['fileDuration'])
				while self.isRecording and (time.time() < (startNow + self.config['video']['fileDuration'])):
					self.controlLights()
					camera.wait_recording(0.5)
					self.lastResponse = 'Recording file: ' + self.currentFile
					if self.config['video']['captureStill'] and time.time() > (lastStill + self.config['video']['stillInterval']):
						print '      capturing still:', stillPath
						camera.capture(stillPath, use_video_port=True)
						lastStill = time.time()
				camera.stop_recording()
				print '		Stop video file:', thisVideoFile

				# convert to mp4
				if self.config['video']['converttomp4']:
					print 'converting to .mp4', thisVideoFile
					self.convertVideo(thisVideoFile, self.config['video']['fps'])
			print 'recordVideoThread() out of while'
			
	'''
	def readTemperature(self):
		humidity = None
		temperature = None
		if g_dhtLoaded:
			if time.time() > self.lastTemperatureTime + self.temperatureInterval:
				pin = self.config['hardware']['temperatureSensor']
				#print 'pin:', pin
				try:
					humidity, temperature = Adafruit_DHT.read(Adafruit_DHT.DHT22, pin)
					if humidity is not None and temperature is not None:
						humidity = math.floor(humidity * 100) / 100
						temperature = math.floor(temperature * 100) / 100
						#print humidity, temperature
						# convert to farenheight
						# temperature = temperature * 9/5.0 + 32
					# set even on fail,
					self.lastTemperatureTime = time.time()
				except:
					print 'readTemperature() exception reading temperature/humidity'
		return humidity, temperature
	'''
	
	#
	# Utility
	#
	def whatismyip(self):
		arg='ip route list'
		p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
		data = p.communicate()
		split_data = data[0].split()
		ipaddr = split_data[split_data.index('src')+1]
		return ipaddr

	# generate a file list of video files
	def make_tree(self, path):
		filelist = []
		for root, dirs, files in os.walk(path):
			for file in files:
				if file.endswith('.h264'):
					filelist.append(file)
		return filelist


