# 20170817
# Robert Cudmore

import os, sys

# append path to ../homecage_app
mypath = os.path.abspath(os.path.dirname(__file__)) # full path to *this file
parentpath = os.path.dirname(mypath) # path to parent folder
homecage_app_path = os.path.join(parentpath, 'homecage_app') # assuming parent folder has homecage_app
sys.path.insert(0, homecage_app_path)


import logging
logger = logging.getLogger('flask.app')

import bUtil
from bTrial import bTrial
from bCamera import bCamera
from version import __version__

class treadmillTrial(bTrial):
	def __init__(self):
		pass
		
class treadmill():

	def __init__(self):
		#self.home = bHome()
		self.trial = treadmillTrial()
		self.camera = bCamera(self.trial)
		
	def startTrial(self):
		# spin up the camera
		
		# wait 0.5 seconds
		
		# tell arduino to start
		
	def stopTrial(self):
		# shutdown camera
		
		# stop trial
		
		# tell arduino to stop
		
if __name__ == '__main__':
	# debugging
	t = treadmill()