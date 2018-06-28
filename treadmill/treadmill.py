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
			# sleep to allow curcular video stream to really get going
			#time.sleep(3)
			# tell arduino to start
			self.treadmill.inSerialQueue.put('start')
		else:
			#logger.warning('startTrial but trial is running')
			pass
			
	def stopTrial(self):

		if self.isRunning:
			super(treadmillTrial, self).stopTrial()
			# tell arduino to stop
			self.treadmill.inSerialQueue.put('stop')
		else:
			#logger.warning('stopTrial but trial is not running')
			pass
			
#########################################################################
class mySerialThread(threading.Thread):
	def __init__(self, inSerialQueue, outSerialQueue, errorSerialQueue, port, baud):
		threading.Thread.__init__(self)
		self.inSerialQueue = inSerialQueue
		self.outSerialQueue = outSerialQueue
		self.errorSerialQueue = errorSerialQueue
		#serialport = '/dev/ttyACM0'
		#serialbaud = 115200
		try:
			# there is no corresponding self.mySerial.close() ???
			self.mySerial = serial.Serial(port, baud, timeout=0.25)
		except (serial.SerialException) as e:
			logger.error(str(e))
			errorSerialQueue.put(str(e))
		except:
			logger.error('other exception in mySerialThread init')
			raise
		#else:
		#	errorSerialQueue.put('None')

	def run(self):
		logger.debug('mySerialThread starting')
		while True:
			try:
				serialCommand = self.inSerialQueue.get(block=False, timeout=0)
			except (queue.Empty) as e:
				pass
			else:
				logger.info('serialThread inSerialQueue: "' + str(serialCommand) + '"')
				
				try:
					if not serialCommand.endswith('\n'):
						serialCommand += '\n'
					self.mySerial.write(serialCommand.encode())
					time.sleep(0.1)
					resp = self.mySerial.readline().decode().strip()
					self.outSerialQueue.put(resp)
					logger.info('serialThread outSerialQueue: "' + str(resp) + '"')
				except (serial.SerialException) as e:
					logger.error(str(e))
				except:
					logger.error('other exception in mySerialThread run')
					raise
		
#########################################################################
class treadmill():

	def __init__(self):
		self.systemInfo = bUtil.getSystemInfo()
		
		self.trial = treadmillTrial(self)

		#
		# background serial thread
		self.serialResponseStr = []
		self.inSerialQueue = queue.Queue() # queue is infinite length
		self.outSerialQueue = queue.Queue()
		self.errorSerialQueue = queue.Queue()
		# create, deamonize and start the serial thread
		port = self.trial.config['hardware']['serial']['port']
		baud = self.trial.config['hardware']['serial']['baud']
		self.mySerialThread = mySerialThread(self.inSerialQueue, self.outSerialQueue, self.errorSerialQueue, port, baud)
		self.mySerialThread.daemon = True
		self.mySerialThread.start()
		
		
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


		while not self.errorSerialQueue.empty():
			serialItem = self.errorSerialQueue.get()
			print('   errorSerialQueue serialItem:', serialItem)
			self.serialResponseStr.append(serialItem)

		while not self.trial.cameraErrorQueue.empty():
			cameraItem = self.trial.cameraErrorQueue.get()
			print('   cameraErrorQueue cameraItem:', cameraItem)
			self.serialResponseStr.append(cameraItem)
			
		status['serialQueue'] = self.serialResponseStr

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

	def startArmVideo(self):
		''' MASTER '''
		logger.debug('startArmVideo')
		#self.trial.startTrial(startArmVideo=True) # starts the video
		if self.trial.camera is not None:
			self.trial.camera.startArmVideo()
					
	def stopArmVideo(self):
		logger.debug('stopArmVideo')
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

		#print('updateMotor()')
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

			serialCommand = 'settrial,' + key + ',' + str(value)
			#print('   send:', serialCommand)
			self.inSerialQueue.put(serialCommand)
		
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
	
	