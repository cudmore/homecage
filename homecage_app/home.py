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

		self.whiteIsOn = 0
		self.irIsOn = 0

		self.isRecording = 0
		self.isStreaming = 0
		
		#self.fps = 30
		#self.resolution = (self.config['video']['resolution'][0], self.config['video']['resolution'][1])
		#self.fileDuration = 5 #5*60
		#self.stillInterval = 2 # sec
		
		#self.lightsOnTime = 6
		#self.lightsOffTime = 18
		
		self.currentFile = 'None'
		self.currentStartSeconds = float('nan')
		self.videoPath = '/home/pi/video/'
		
		self.ip = self.whatismyip()
		self.lastResponse = ''
		
		self.streamWidth = 1024
		self.streamHeight = 768

		
	def loadConfigFile(self):
		with open('config.json') as configFile:
			config = json.load(configFile)
		return config
	
	def saveConfigFile(self):
		with open('config.json', 'w') as outfile:
			json.dump(self.config, outfile)
	
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
				#self.currentStartSeconds = time.time()
				#self.currentFile = datetime.now().strftime('%Y%m%d_%H%M%S')
				# start a background thread
				thread = threading.Thread(target=self.recordVideoThread, args=())
				thread.daemon = True							# Daemonize thread
				thread.start()								  # Start the execution
			else:
				self.currentStartSeconds = float('nan')
				self.currentFile = 'None'
				# turn off lights
				self.whiteLED(0)
				self.irLED(0)

			self.lastResponse = 'Recording is ' + ('on' if onoff else 'off')
		
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

	def irLED(self,onoff, allow=False):
		# pass allow=true to control light during recording
		if not allow and self.isRecording:
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
				thisVideoFile = self.videoPath + self.currentFile
	
				print '   Start video file:', self.currentFile
	
				camera.start_recording(thisVideoFile)
				#camera.wait_recording(self.config['video']['fileDuration'])
				while self.isRecording and (time.time() < (startNow + self.config['video']['fileDuration'])):
					self.controlLights()
					camera.wait_recording(0.5)
					self.lastResponse = 'Recording file: ' + self.currentFile
					if self.config['video']['captureStill'] and time.time() > (lastStill + self.config['video']['stillInterval']):
						print 'capturing still:'
						camera.capture(stillPath, use_video_port=True)
						lastStill = time.time()
				camera.stop_recording()
				print '	  Stop video file:', thisVideoFile
			print 'recordVideoThread() out of while'

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

	def make_tree(self, path):
		filelist = []
		for root, dirs, files in os.walk(path):
			for file in files:
				if file.endswith('.h264'):
					filelist.append({'name': file})
		return filelist


