# 20170817
# Robert Cudmore

import os, sys, time
from collections import OrderedDict
from pprint import pprint
import serial
import threading, queue

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
			#self.treadmill.sendtoserial('start')
			serialDict = {}
			serialDict['commandType'] = 'oneCommand'
			serialDict['serialCommands'] = 'start'
			self.treadmill.inSerialQueue.put(serialDict)
		else:
			logger.debug('startTrial but trial is running')
			
	def stopTrial(self):

		if self.isRunning:
			super(treadmillTrial, self).stopTrial()
		
			#
			#self.treadmill.sendtoserial('d')
			#self.treadmill.sendtoserial('stop')
			serialDict = {}
			serialDict['commandType'] = 'oneCommand'
			serialDict['serialCommands'] = 'stop'
			self.treadmill.inSerialQueue.put(serialDict)
		else:
			logger.debug('stopTrial but trial is not running')

#########################################################################
class treadmill():

	def __init__(self):
		self.systemInfo = bUtil.getSystemInfo()
		
		self.trial = treadmillTrial(self)
		#self.trial = bTrial()

		#
		# background serial thread
		self.serialResponseStr = []
		self.inSerialQueue = queue.Queue() # queue is infinite length
		self.outSerialQueue = queue.Queue()
		self.errorSerialQueue = queue.Queue()
		self.startSerialThread()

		"""self.serial = None # serial port connection to teensy/arduino
		self.serialError = ''
		"""
		
	#########################################################################
	# status
	#########################################################################
	def getStatus(self):
		status = OrderedDict()
		
		status['systemInfo'] = self.systemInfo # remember to update occasionally
		status['trial'] = self.trial.getStatus()

		while not self.outSerialQueue.empty():
			serialItem = self.outSerialQueue.get()
			#print('   serialItem:', serialItem)
			self.serialResponseStr.append(serialItem)
		status['serialQueue'] = self.serialResponseStr

		#print("status['serialQueue']:", status['serialQueue'])
		
		#status['serialError'] = self.serialError
		
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
	# serial thread
	#########################################################################
	def startSerialThread(self):
		thread = threading.Thread(target=self.serialThread, args=(self.inSerialQueue,self.outSerialQueue,self.errorSerialQueue,))
		thread.daemon = True							# Daemonize thread
		thread.start()									# Start the execution

	def serialThread(self, inSerialQueue, outSerialQueue, errorSerialQueue):
		while True:
			try:
				cmd = inSerialQueue.get(block=False, timeout=0)
			except (queue.Empty) as e:
				pass
			else:
				#print('queue not empty')
				logger.info('serialThread inSerialQueus:' + str(cmd))
				serialport = '/dev/ttyACM0'
				serialbaud = 115200
				
				if cmd['commandType'] == 'motorDict':
					# open serial once and send multiple commands
					mySerial = serial.Serial(serialport, serialbaud, timeout=0.25)
					for key, value in cmd['serialCommands'].items():
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
						#self.serial_settrial(key, value)

						serialCommand = 'settrial,' + key + ',' + str(value)
						print('=== serialThread motorDict writing to serial ')
						print('send:', serialCommand)
						serialCommand += '\n'
						serialCommand = serialCommand.encode() # python 3, does it work in python 2 ?
						mySerial.write(serialCommand)
						resp = mySerial.readline().decode()
						print('resp:', resp.strip())
						#resp += '\n'
						outSerialQueue.put(resp)
						
						time.sleep(0.01)
					mySerial.close()
					
				elif cmd['commandType'] == 'oneCommand':
					# send one command
					mySerial = serial.Serial(serialport, serialbaud, timeout=0.25)
					resp = ''
					if cmd['serialCommands'] =='start':
						# start trial
						mySerial.write('start\n'.encode()) # encode() for python 3.x, what about 2.x ?
						#theRet = self.emptySerial_thread(mySerial)
						resp = mySerial.readline().decode()
					if cmd['serialCommands'] =='stop':
						# start trial
						mySerial.write('stop\n'.encode()) # encode() for python 3.x, what about 2.x ?
						#theRet = self.emptySerial_thread(mySerial)
						resp = mySerial.readline().decode()

					if cmd['serialCommands'] == 'd': #dump trial
						mySerial.write('d\n'.encode()) # encode() for python 3.x, what about 2.x ?
						#theRet = self.emptySerial_thread(mySerial)
					if cmd['serialCommands'] == 'p': #print params
						mySerial.write('p\n'.encode())
						#theRet = self.emptySerial_thread(mySerial)
					if cmd['serialCommands'] == 'v': #version
						mySerial.write('v\n'.encode())
						#theRet = self.emptySerial_thread(mySerial)
					#theRetStr = ''.join(theRet) # convert string list to string

					print('resp:', resp)
					if resp:
						outSerialQueue.put(resp)

					mySerial.close()

				else:
					# error
					print('*** ERROR: serialThread() received unkonw command:', cmd)
					
			time.sleep(0.2)

	def emptySerial_thread(self, serial):
		'''
		if self.trialRunning:
			print('warning: trial is already running')
			return 0
		'''
		
		theRet = ''
		if serial:
			try:
				line = serial.readline()
				i = 0
				while line:
					line = line.rstrip()
					theRet += line + '\n'
					#self.NewSerialData(line)
					line = serial.readline()
					i += 1
			except (serial.serialutil.SerialException) as e:
				print('\n\nexcept emptySerial_thread')
				logger.error(str(e))
				raise
			except:
				print('\n\nOTHER except emptySerial_thread\n\n')
				raise
							
		return theRet	
			
	#########################################################################
	# Serial communication with teensy/arduino
	#########################################################################
	def updateMotor(self, motorDict):
		""" todo: put this in bTrial """

		#self.serial_settrial2(motorDict)
		serialDict = {}
		serialDict['commandType'] = 'motorDict'
		serialDict['serialCommands'] = motorDict
		self.inSerialQueue.put(serialDict)
		
		newFileDuration = motorDict['motorNumEpochs'] * motorDict['motorRepeatDuration']
				
		# motorRepeatDuration (ms) -->> fileDuration (sec)
		newFileDuration /= 1000
		
		self.trial.config['trial']['repeatInfinity'] = False
		self.trial.config['trial']['numberOfRepeats'] = 1
		self.trial.config['trial']['repeatDuration'] = newFileDuration

		self.trial.config['motor'] = motorDict
		# convert ['updateMotor'] to (-1, +1)
		
		
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
	
	