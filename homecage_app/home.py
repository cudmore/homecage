# Robert Cudore
# 20171103

import os, time, math
import subprocess
import threading
from datetime import datetime
from collections import OrderedDict
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
		print 'Initializing home.py'
		
		self.config = self.loadConfigFile()
		
		GPIO.setmode(GPIO.BCM)

		GPIO.setwarnings(False)

		GPIO.setup(self.config['hardware']['whiteLightPin'], GPIO.OUT)
		GPIO.setup(self.config['hardware']['irLightPin'], GPIO.OUT)

		GPIO.output(self.config['hardware']['whiteLightPin'], 0)
		GPIO.output(self.config['hardware']['irLightPin'], 0)

		self.whiteIsOn = False
		self.irIsOn = False

		self.isRecording = False
		self.isStreaming = False
		
		self.currentFile = 'None'
		self.currentStartSeconds = float('nan')
		self.videoPath = self.config['video']['savepath']
		self.saveVideoPath = '' # set when we start video recording
		
		self.lastStillTime = '' # time.time()
		
		self.ip = self.whatismyip()
		self.lastResponse = ''
		
		#self.streamWidth = 1024
		#self.streamHeight = 768

		# temperature and humidity
		self.lastTemperatureTime = 0
		self.lastTemperature = None
		self.lastHumidity = None
		
		if g_dhtLoaded and self.config['hardware']['readtemperature']>0:
			print '   Initialized DHT temperature sensor'
			GPIO.setup(self.config['hardware']['temperatureSensor'], GPIO.IN)
			myThread = threading.Thread(target = self.tempThread)
			myThread.daemon = True
			myThread.start()
		else:
			print '   Did not find DHT temperature sensor'
			
		if not os.path.isdir(self.videoPath):
			os.makedirs(self.videoPath)
			
		# get the raspberry pi version, we can run on version 2/3, on model B streaming does not work
		cmd = 'cat /proc/device-tree/model'
		child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
		out, err = child.communicate() # out is something like 'Raspberry Pi 2 Model B Rev 1.1'
		print 'out:', out
		goodModels = ["Raspberry Pi 2", "Rapsberry Pi 3"]
		found = [a for a in goodModels if a in out]
		if len(found)>0:
			print '   Good: Running on a:', out
		else:
			print '   Warning: You are running on a potentially unsupported Pi, please use either 2 or 3'
		self.raspberryModel = out
		
		# get the version of Raspian, we want to be running on Jessie or Stretch
		import platform
		dist = platform.dist() # 8 is jessie, 9 is stretch
		if len(dist)==3:
			if float(dist[1]) >= 8:
				print '   Good: running on Jessie, Stretch or above'
			else:
				print '   Warning: not designed to work on Raspina before Jesiie'
		
		print '   Done initializing home.py'
		
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
		print 'setParam()', param, value, 'type:', type(value)
		one, two = param.split('.')
		if one not in self.config:
			# error
			print 'ERROR: setParam() did not find', one, 'in self.config'
			return
		if two not in self.config[one]:
			# error
			print 'ERROR: setParam() did not find', two, 'in self.config["', one, '"]'
			return
			
		print '   was:', self.config[one][two], 'type:', type(self.config[one][two])
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
		
		print '   now:', self.config[one][two], 'type:', type(self.config[one][two])
		
	def loadConfigDefaultsFile(self):
		print 'home.py loadConfigDefaultsFile()'
		with open('config_defaults.json') as configFile:
			self.config = json.load(configFile)
		self.lastResponse = 'Loaded default options file'
	
	def loadConfigFile(self):
		with open('config.json') as configFile:
			config = json.load(configFile, object_pairs_hook=OrderedDict)
		return config
	
	def saveConfigFile(self):
		print 'home.py saveConfigFile()'
		with open('config.json', 'w') as outfile:
			json.dump(self.config, outfile, indent=4)
		self.lastResponse = 'Saved options file'
	
	def getStatus(self):
		# return the status of the server, all params
		# is called at a short interval, ~1 sec

		now = datetime.now()
				
		status = OrderedDict()

		status['date'] = now.strftime('%Y-%m-%d')
		status['time'] = now.strftime('%H:%M:%S')
		status['ip'] = self.ip
		status['hostname'] = socket.gethostname()

		status['isRecording'] = self.isRecording
		status['isStreaming'] = self.isStreaming
		status['irLED'] = self.irIsOn
		status['whiteLED'] = self.whiteIsOn

		status['currentFile'] = self.currentFile
		if self.isRecording and self.currentStartSeconds>0:
			status['timeRemaining'] = round(self.config['video']['fileDuration'] - (time.time() - self.currentStartSeconds),2)
		else:
			status['timeRemaining'] = 'n/a'
			
		status['lastResponse'] = self.lastResponse # filled in by each route

		status['lastStillTime'] = self.lastStillTime
		
		#
		#filelist = self.make_tree('/home/pi/video')
		#status['videofilelist'] = json.dumps(filelist)
		
		# temperature and humidity
		status['temperature'] = self.lastTemperature
		status['humidity'] = self.lastHumidity
			
		return status

	def getConfig(self):
		# parameters that can be set by user
		return self.config
		
	def record(self,onoff):
		# sart and stop video recording
		if self.isStreaming:
			self.lastResponse = 'Recording not allowed during streaming'
		else:
			self.isRecording = onoff
			if self.isRecording:
				# set output path
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d')
				self.saveVideoPath = self.videoPath + '/' + startTimeStr + '/'
				print 'home.record() is making output directory:', self.saveVideoPath
				if not os.path.isdir(self.saveVideoPath):
					os.makedirs(self.saveVideoPath)
								
				# start a background thread
				thread = threading.Thread(target=self.recordVideoThread, args=())
				thread.daemon = True							# Daemonize thread
				thread.start()									# Start the execution
			else:
				self.currentStartSeconds = float('nan')
				# this is set when the thread actually exits
				#self.currentFile = 'None'
				# turn off lights
				if self.config['lights']['auto']:
					self.whiteLED(False)
					self.irLED(False)

			self.lastResponse = 'Recording is ' + ('on' if onoff else 'off')
	
	def convertVideo(self, videoFilePath, fps):
		# at end of video recording, convert h264 to mp4
		# also build a db.txt with videos in a folder
		print 'convertVideo()', videoFilePath, fps
		cmd = './convert_video.sh ' + videoFilePath + ' ' + str(fps)
		child = subprocess.Popen(cmd, shell=True)
		out, err = child.communicate()
		#print 'out:', out
		#print 'err:', err
		
		# append to dict and save in file
		dirname = os.path.dirname(videoFilePath) 
		mp4File = os.path.basename(videoFilePath).split('.')[0] + '.mp4'
		mp4Path = os.path.join(dirname, mp4File)
		print 'mp4Path:', mp4Path
		command = "avprobe -show_format -show_streams -loglevel 'quiet' " + str(mp4Path) + ' -of json'
		#command = "avprobe -show_format -show_streams " + str(mp4Path) + ' -of json'
		print command
		p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
		data = p.communicate()
		data = json.loads((data[0]))
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
		print 'dbFile:', dbFile
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
		
	def stream(self,onoff):
		# start and stop video stream
		print 'stream()'
		if self.isRecording:
			self.lastResponse = 'Streaming not allowed during recording'
		else:
			self.isStreaming = onoff
			self.log('stream', '', '', self.isStreaming)
			if self.isStreaming:
				width = self.config['stream']['resolution'].split(',')[0]
				height = self.config['stream']['resolution'].split(',')[1]
				cmd = './stream start ' \
					+ width \
					+ ' ' \
					+ height
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
		if self.config['lights']['auto'] and not allow and self.isRecording:
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
		if self.config['lights']['auto'] and not allow and self.isRecording:
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
			while self.isRecording:
				startNow = time.time()
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d_%H%M%S')

				#the file we are about to record/save
				self.currentFile = startTimeStr + '.h264'
				self.currentStartSeconds = time.time()
				thisVideoFile = self.saveVideoPath + self.currentFile
	
				print '   Start video file:', self.currentFile
				self.log('video', thisVideoFile, self.currentFile, True)
	
				camera.start_recording(thisVideoFile)
				while self.isRecording and (time.time() < (startNow + self.config['video']['fileDuration'])):
					self.controlLights()
					camera.wait_recording(0.3)
					self.lastResponse = 'Recording file: ' + self.currentFile
					if self.config['video']['captureStill'] and time.time() > (lastStill + self.config['video']['stillInterval']):
						print '   capturing still:', stillPath
						camera.capture(stillPath, use_video_port=True)
						lastStill = time.time()
						self.lastStillTime = datetime.now().strftime('%Y%m%d %H:%M:%S')
				camera.stop_recording()
				self.log('video', thisVideoFile, self.currentFile, False)
				self.currentFile = 'None'
				print '   Stop video file:', thisVideoFile

				# convert to mp4
				if self.config['video']['converttomp4']:
					print '   Converting to .mp4', thisVideoFile
					self.lastResponse = 'Converting to mp4'
					self.convertVideo(thisVideoFile, self.config['video']['fps'])
					self.lastResponse = ''
			print 'recordVideoThread() out of while'

	def tempThread(self):
		# thread to run temperature/humidity in backfround
		# dht is blocking, long delay cause delays in web interface
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


