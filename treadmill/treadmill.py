# 20170817
# Robert Cudmore

import os, sys
from collections import OrderedDict

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
	def __init__(self):
		super(treadmillTrial, self).__init__()
		
		self.trial['motor'] = OrderedDict()
		self.trial['motor']['delay'] = 7000
		self.trial['motor']['duration'] = 7000
		self.trial['motor']['speed'] = 100
		self.trial['motor']['direction'] = 1
		
	def startTrial(self, slave=False, now=None):
		super(treadmillTrial, self).startTrial(slave=slave, now=now)
		
		logger.debug('FIRE UP ARDUINO')
		
	def stopTrial(self):
		super(treadmillTrial, self).stopTrial()
		
		logger.debug('SHUT DOWN ARDUINO')
		
#########################################################################
class treadmill():

	def __init__(self):
		self.systemInfo = bUtil.getSystemInfo()
		
		self.trial = treadmillTrial()
		#self.camera = bCamera(self.trial)
		
	def getStatus(self):
		status = OrderedDict()
		
		status['systemInfo'] = self.systemInfo # remember to update occasionally
		status['trial'] = self.trial.getStatus()
		
		return status
		
	def startArm(self):
		self.trial.camera.arm(True)
		
	def stopArm(self):
		self.trial.camera.arm(False)
		
	def startTrial(self):
		''' MASTER '''
		self.trial.startTrial() # starts the video
		
	def stopTrial(self):
		''' MASTER '''
		self.trial.stopTrial() # stops the video
		
if __name__ == '__main__':
	# debugging
	t = treadmill()