# 20170817
# Robert Cudmore

import os, sys

# append path to ../homecage_app
mypath = os.path.abspath(os.path.dirname(__file__)) # full path to *this file
parentpath = os.path.dirname(mypath) # path to parent folder
homecage_app_path = os.path.join(parentpath, 'homecage_app') # assuming parent folder has homecage_app
sys.path.append(homecage_app_path)

from homecage_app import home

import logging
logger = logging.getLogger('flask.app')

class bTreadmill():

	def __init__(self):
		self.home = home.home()
		pass
		
if __name__ == '__main__':
	# debugging
	t = bTreadmill()