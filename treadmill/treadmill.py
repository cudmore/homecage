# 20170817
# Robert Cudmore

import os, sys, time
from collections import OrderedDict
from pprint import pprint
import serial

# eventually import from homecage
# to begin I am working on copies of (bTrial, bCamera, bUtil) in treadmill/
'''
# append path to ../homecage_app
mypath = os.path.abspath(os.path.dirname(__file__)) # full path to *this file
parentpath = os.path.dirname(mypath) # path to parent folder
homecage_app_path = os.path.join(parentpath, 'homecage_app') # assuming parent folder has homecage_app
sys.path.insert(0, homecage_app_path)
'''

import logging
logger = logging.getLogger('flask.app')

import bUtil
from bTrial import bTrial
from bCamera import bCamera
from version import __version__

#########################################################################
class treadmillTrial(bTrial):
	def __init__(self, treadmill):
		super(treadmillTrial, self).__init__()
		
		self.treadmill = treadmill
		
	def startTrial(self, startArmVideo=False, now=None):
		if not self.isRunning:
			super(treadmillTrial, self).startTrial(startArmVideo=startArmVideo, now=now)
			
			# sleep to allow curcular stream to really get going
			#time.sleep(3)
			
			# tell arduino to start
			self.treadmill.sendtoserial('start')
		else:
			logger.debug('startTrial but trial is running')
			
	def stopTrial(self):

		if self.isRunning:
			super(treadmillTrial, self).stopTrial()
		
			#
			#self.treadmill.sendtoserial('d')
			self.treadmill.sendtoserial('stop')
		else:
			logger.debug('stopTrial but trial is not running')

#########################################################################
class treadmill():

	def __init__(self):
		self.systemInfo = bUtil.getSystemInfo()
		
		self.trial = treadmillTrial(self)
		#self.trial = bTrial()

		self.serial = None # serial port connection to teensy/arduino
		self.serialError = ''
		
	def getStatus(self):
		status = OrderedDict()
		
		status['systemInfo'] = self.systemInfo # remember to update occasionally
		status['trial'] = self.trial.getStatus()
		status['serialError'] = self.serialError
		
		return status
		
	#########################################################################
	# Start/Stop
	#########################################################################
	def startRecord(self):
		self.trial.startTrial() # starts the video
		
	def stopRecord(self):
		self.trial.stopTrial() # stops the video

	def startStream(self):
		if self.trial.camera:
			self.trial.camera.stream(True)
		
	def stopStream(self):
		if self.trial.camera:
			self.trial.camera.stream(False)

	def startArm(self):
		# turn off repeat infinity, set num repeats = 1
		self.trial.config['trial']['repeatInfinity'] = False
		self.trial.config['trial']['numberOfRepeats'] = 1
		
		if self.trial.camera:
			self.trial.camera.arm(True)
		
	def stopArm(self):
		if self.trial.camera:
			self.trial.camera.arm(False)

	def startTrial(self):
		''' MASTER '''
		logger.debug('startTrial')
		#self.trial.startTrial(startArmVideo=True) # starts the video
		if self.trial.camera is not None:
			self.trial.camera.startArmVideo()
					
	def stopTrial(self):
		logger.debug('stopTrial')
		''' MASTER '''
		#self.trial.stopTrial() # stops the video
		if self.trial.camera is not None:
			self.trial.camera.stopArmVideo()

		
	#########################################################################
	# update config
	#########################################################################
	def saveConfig(self):
		self.trial.saveConfig()
		
	def updateConfig(self, configDict):
		self.trial.updateConfig(configDict)
		
	def updateAnimal(self, configDict):
		self.trial.updateAnimal(configDict)
		
	def updateLED(self, configDict):
		self.trial.updateLED(configDict)
		
	#########################################################################
	# Serial communication with teensy/arduino
	#########################################################################
	def updateMotor(self, motorDict):
		""" todo: put this in bTrial """

		self.serial_settrial2(motorDict)

		newFileDuration = motorDict['motorNumEpochs'] * motorDict['motorRepeatDuration']
				
		# motorRepeatDuration (ms) -->> fileDuration (sec)
		newFileDuration /= 1000
		
		self.trial.config['trial']['repeatInfinity'] = False
		self.trial.config['trial']['numberOfRepeats'] = 1
		self.trial.config['trial']['repeatDuration'] = newFileDuration

		self.trial.config['motor'] = motorDict
		# convert ['updateMotor'] to (-1, +1)
		
	def serial_settrial2(self,motorDict):
		print('treadmill.serial_settrial2()', motorDict)

		'''
		if self.trialRunning:
			print 'warning: trial is running -->> no action taken'
			return 0
		'''

		serialport  = self.trial.config['hardware']['serial']['port'] #'/dev/ttyACM0'
		serialbaud = self.trial.config['hardware']['serial']['baud'] #115200

		try:
			self.serial = serial.Serial(serialport, serialbaud, timeout=0.25)
	
			for key, value in motorDict.items():
				#convert python based variable to arduino
				if key == 'motorNumEpochs':
					key = 'numEpoch'
				if key == 'motorRepeatDuration':
					key = 'epochDur'
				"""
				if key == 'motorRepeatDuration':
					key = 'epochDur'
				if key == 'motorRepeatDuration':
					key = 'epochDur'
				"""
				self.serial_settrial(key, value)
				time.sleep(0.01)
	
			self.serial.close()
			self.serial = None
			self.serialError = ''
		except (serial.SerialException) as e:
			self.serialError = 'Error opening serial port ' + serialport
			logger.error('serial.SerialException')
			raise
						
	def serial_settrial(self, key, val):
		'''
		set value for *this
		send serial to set value on arduino
		'''
		
		'''
		if self.trialRunning:
			print 'warning: trial is running -->> no action taken'
			return 0
		'''
		
		#print "=== treadmill.settrial() key:'" + key + "' val:'" + val + "'"
		'''
		put sanit check back in
		'''
		if 1: # key in self.trialParam:
			'''
			todo: put back in
			self.trialParam[key] = val
			'''
			serialCommand = 'settrial,' + key + ',' + str(val)
			#serialCommand = str(serialCommand)
			print('=== treadmill.settrial() writing to serial ')
			print('send:', serialCommand)
			serialCommand += '\n'
			serialCommand = serialCommand.encode() # python 3, does it work in python 2 ?
			self.serial.write(serialCommand)
			
			''' might want to capture response to double check?
			send: settrial,epochDur,1000
			receive: trial.epochDur=1000
			'''
			resp = self.serial.readline()
			print('resp:', resp.strip())
			
			'''
			todo: put back in, not really needed
			self.updatetrialdur()
			'''
		else:
			print('\tERROR: treadmill:settrial() did not find', key, 'in trialParam dict')
			
	def sendtoserial(self, this):
		theRet = None
		
		serialport  = self.trial.config['hardware']['serial']['port'] #'/dev/ttyACM0'
		serialbaud = self.trial.config['hardware']['serial']['baud'] #115200
		
		try:
			self.serial = serial.Serial(serialport, serialbaud, timeout=0.25)
		
			time.sleep(.02)
		
			throwout = self.emptySerial()
		
			#time.sleep(.02)

			if this =='start':
				# start trial
				self.serial.write('start\n'.encode()) # encode() for python 3.x, what about 2.x ?
				theRet = self.emptySerial()
			if this =='stop':
				# start trial
				self.serial.write('stop\n'.encode()) # encode() for python 3.x, what about 2.x ?
				theRet = self.emptySerial()

			if this == 'd': #dump trial
				self.serial.write('d\n'.encode()) # encode() for python 3.x, what about 2.x ?
				theRet = self.emptySerial()
			if this == 'p': #print params
				self.serial.write('p\n'.encode())
				theRet = self.emptySerial()
			if this == 'v': #version
				self.serial.write('v\n'.encode())
				theRet = self.emptySerial()
		
			print('=== done sendtoserial this:', this, 'theRet:', theRet)
		
			#close serial
			self.serial.close()
			self.serial = None
		except:
			print('\n\nexcept sendtoserial this:', this, 'theRet:', theRet, '\n\n')
			raise
					
		return theRet

	def emptySerial(self):
		'''
		if self.trialRunning:
			print('warning: trial is already running')
			return 0
		'''
		
		theRet = []
		if self.serial:
			try:
				line = self.serial.readline()
				i = 0
				while line:
					line = line.rstrip()
					theRet.append(line)
					#self.NewSerialData(line)
					line = self.serial.readline()
					i += 1
			except (serial.serialutil.SerialException) as e:
				print('\n\nexcept emptySerial')
				logger.error(str(e))
				raise
			except:
				print('\n\nOTHER except emptySerial\n\n')
				raise
							
		return theRet	
		
#########################################################################
if __name__ == '__main__':
	# debugging
	t = treadmill()
	
	# debug serieal
	r = t.sendtoserial('p')
	print('params:', r)
	r = t.sendtoserial('v')
	print('version:', r)
	r = t.sendtoserial('d')
	print('trial:', r)
	
	'''
	These are the parameter names used by version 20160918 of teensy code
	
	[b'trialNumber=0',
		b'trialDur=1700', # DON'T set this one, it is calculated
		b'motorNumEpochs=3',
		b'epochDur=500',
		b'preDur=100',
		b'postDur=100',
		b'useMotor=0',
		b'motorDel=100',
		b'motorDur=300',
		b'motorSpeed=0',
		b'motorMaxSpeed=1000',
		b'versionStr=20160918']
	'''
	trialDict = {'epochDur': 1000, 'motorNumEpochs': 1, 'badkey': 'badvalue'}
	t.serial_settrial2(trialDict)
	
	