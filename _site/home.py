#global object for homecage video and sensors
#
#Usage:
#import home
#h = home.home()
#h.white(1)

#20160706 : updated to re-install for Valerie
#			now using Adafruit_DHT

import os, time, datetime, math
import RPi.GPIO as GPIO
import Adafruit_DHT
#import dhtreader #requires dhtreader.so in same directory as *this

class MyException(Exception):
	pass

class home:
	def __init__(self):
		self.init()

	def init(self):
		GPIO.setmode(GPIO.BCM)

		#lights
		self.irLightPin = 7
		self.whiteLightPin = 8

		GPIO.setwarnings(False)

		GPIO.setup(self.whiteLightPin, GPIO.OUT)
		GPIO.setup(self.irLightPin, GPIO.OUT)

		GPIO.output(self.whiteLightPin, 0)
		GPIO.output(self.irLightPin, 0)

		self.whiteIsOn = 0
		self.irIsOn = 0

		#temp and hum
		self.dhttype = Adafruit_DHT.DHT22 #22
		self.dhtpin = 17
		#dhtreader.init()

		#
		#running wheels
		self.hallSensor1 = 23 #wheel 1, sensor 1
		self.hallSensor2 = 24 #wheel 1, sensor 2

		self.hallSensor3 = 14 #wheel 1, sensor 1
		self.hallSensor4 = 15 #wheel 1, sensor 1
		
		#sensor is always on and turn off in response to a magnet, use GPIO.PUD_UP
		GPIO.setup(self.hallSensor1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.hallSensor2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.hallSensor3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.setup(self.hallSensor4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

		#sensors is always on, detect FALLING phase with GPIO.FALLING
		GPIO.add_event_detect(self.hallSensor1, GPIO.FALLING)
		GPIO.add_event_callback(self.hallSensor1, self.wheel_event_received)

		GPIO.add_event_detect(self.hallSensor2, GPIO.FALLING)
		GPIO.add_event_callback(self.hallSensor2, self.wheel_event_received)

		GPIO.add_event_detect(self.hallSensor3, GPIO.FALLING)
		GPIO.add_event_callback(self.hallSensor3, self.wheel_event_received)

		GPIO.add_event_detect(self.hallSensor4, GPIO.FALLING)
		GPIO.add_event_callback(self.hallSensor4, self.wheel_event_received)
	
		#
		#log file
		self.logFile = None
		#self.log = {'a': [], 'b': []}

	def wheel_event_received(self, channel):
		"""callback embedded with GPIO.add_event_callback()"""
		ts = self.timestamp()
		#print 'channel=', channel
		#wheel 1
		#if GPIO.input(self.hallSensor1):
		if channel == self.hallSensor1:
			#log_wheel_turn(1)
			print 'wheel 1, sensor 1'
			#self.log_append(ts, 'wheel1', 1, 0)
			self.logfile_write(ts, 'wheel1', 1, 0) #save to file
		#if GPIO.input(self.hallSensor2):
		if channel == self.hallSensor2:
			#log_wheel_turn(2)
			print 'wheel 1, sensor 2'
			#self.log_append(ts, 'wheel1', 0, 1)
			self.logfile_write(ts, 'wheel1', 0, 1) #save to file
		#wheel 2
		#if GPIO.input(self.hallSensor3):
		if channel == self.hallSensor3:
			#log_wheel_turn(1)
			print 'wheel 2, sensor 1'
			#self.log_append(ts, 'wheel1', 1, 0)
			self.logfile_write(ts, 'wheel2', 1, 0) #save to file
		#if GPIO.input(self.hallSensor4):
		if channel == self.hallSensor4:
			#log_wheel_turn(2)
			print 'wheel 2, sensor 2'
			#self.log_append(ts, 'wheel2', 0, 1)
			self.logfile_write(ts, 'wheel2', 0, 1) #save to file

	def white(self, *on):
		"""Turn white light on/off or query white light status"""
		if len(on) == 1 and self.whiteIsOn != on[0]:
			GPIO.output(self.whiteLightPin, on[0])
			self.whiteIsOn = on[0] #need [0] otherside lhs becomes tuple
			#self.logfile_write(self.timestamp(), 'whitelight', on[0], [])
		elif len(on) == 0:
			return self.whiteIsOn

	def ir(self, *on):
		"""Turn IR light on/off or query IR light status"""
		if len(on) == 1 and self.irIsOn != on[0]:
			GPIO.output(self.irLightPin, on[0])
			self.irIsOn = on[0] #need [0] otherside lhs becomes tuple
			#self.logfile_write(self.timestamp(), 'irlight', on[0], [])
		elif len(on) == 0:
			return self.irIsOn

	def temperature(self):
		"""Return (temparature, humidity)"""
		try:
			#t, h = dhtreader.read(self.dhttype,self.dhtpin)
			t, h = Adafruit_DHT.read(self.dhttype,self.dhtpin)
			t = math.floor(t * 100) / 100 #round to 2 decimal places
			h = math.floor(h * 100) / 100
			return (t, h)
		except TypeError:
			d,t,s = self.timestamp()
			#print '   ', d, '\t', t, '\terror reading temperature/humidity\n'
			return ('', '')
		except:
			raise

	def timestamp(self):
		"""return (yymmdd, hh:mm:ss, seconds)"""
		now = time.time()
		nowLocal = time.localtime(now)
		theDate = time.strftime("%Y%m%d", nowLocal)
		theTime = time.strftime("%H:%M:%S", nowLocal)	
		return (theDate, theTime, now)

	'''
	def log_append(self, ts, event, val1, val2):
		"""append an event to self.log"""
		if not ts:
			ts = self.timestamp()
		#save to file

		#will be sent to webserver
		#self.log['a'].append([ts[0], ts[1], ts[2], event, val1, val2])
	'''
	
	def log_print(self):
		for line in self.log['a']:
			#print ','.join(map(str,line))
			print line

	def logfile_new(self):
		now = datetime.datetime.now()
		ts1 = now.strftime('%Y%m%d_%H%M%S')
		dateStr = now.strftime('%Y%m%d')
		dstDir = '/home/pi/video/' + dateStr + '/'
		if not os.path.exists(dstDir):
			os.makedirs(dstDir)
		self.logFile = dstDir + ts1 + '.txt'
	
	def logfile_open_old(self):
		try:
			now = datetime.datetime.now()
			ts1 = now.strftime('%Y%m%d_%H%M%S')
			dateStr = now.strftime('%Y%m%d')
			dstDir = '/home/pi/video/' + dateStr + '/'
			if not os.path.exists(dstDir):
				os.makedirs(dstDir)
			dstFile = dstDir + ts1 + '.txt'
			self.outfile = open(dstFile, 'w')
			#header
			self.outfile.write('date,time,seconds,event,v1,v2\n')
			self.logfile_write(self.timestamp(), 'start', 1, 1) #log the start time
		except:
			print 'ERROR: logfile_open() failed, file is', dstFile

	def logfile_write(self, ts, event, v1, v2):
		"""write event to local file"""
		try:
			with open(self.logFile, 'a') as f:
				#self.log_append(ts, event, v1, v2) #append to log for push to server
				f.write(ts[0] + ',' + ts[1] + ',' + str(ts[2]) + ',' + event + ',' + str(v1) + ',' + str(v2) + '\n')
		except:
			print 'ERROR: logfile_write() fail.'
	
	def logfile_close(self):
		#now = datetime.datetime.now()
		#ts1 = now.strftime('%Y%m%d_%H%M%S')
		#dateStr = now.strftime('%Y%m%d')
		ts = self.timestamp()
		self.logfile_write(ts, 'stopped', 1, 1) #log the stop time
		