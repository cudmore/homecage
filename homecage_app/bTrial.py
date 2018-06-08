# Robert H Cudmore
# 20180525

import os, time, json
from collections import OrderedDict

import logging
logger = logging.getLogger('flask.app')

#########################################################################
class bTrial:
	def __init__(self):
		self.trialNum = 0
		
		self.lastResponse = ''
		
		self.trial = OrderedDict()
		self.trial['isRunning'] = False
		self.trial['startTimeSeconds'] = None
		self.trial['startTimeStr'] = ''
		self.trial['dateStr'] = ''
		self.trial['timeStr'] = ''

		self.trial['trialNum'] = None

		self.trial['currentEpoch'] = None
		self.trial['lastEpochSeconds'] = None # start time of epoch

		self.trial['eventTypes'] = []
		self.trial['eventValues'] = []
		self.trial['eventTimes'] = [] # relative to self.trial['startTimeSeconds']

		self.trial['currentFile'] = ''
		self.trial['lastStillTime'] = None

		self.trial['hostnameID'] = ''
		self.trial['animalID'] = ''
		self.trial['conditionID'] = ''
		
	def setHostname(self, hostnameID):
		self.trial['hostnameID'] = hostnameID
		
	def setAnimalID(self, animalID):
		self.trial['animalID'] = animalID
		
	def setConditionID(self, conditionID):
		self.trial['conditionID'] = conditionID
		
	def startTrial(self, now=time.time()):
		logger.debug('startTrial now:' + str(now))
		self.trialNum += 1
		
		self.trial['isRunning'] = True
		self.trial['startTimeSeconds'] = now
		self.trial['startTimeStr'] = time.strftime('%Y%m%d_%H%M%S', time.localtime(now)) 
		self.trial['dateStr'] = time.strftime('%Y%m%d', time.localtime(now))
		self.trial['timeStr'] = time.strftime('%H:%M:%S', time.localtime(now))

		self.trial['trialNum'] = self.trialNum
		
		self.trial['currentEpoch'] = 0
		self.trial['lastEpochSeconds'] = now
		
		self.trial['eventTypes'] = []
		self.trial['eventValues'] = []
		self.trial['eventTimes'] = [] # relative to self.trial['startTimeSeconds']
		
		self.trial['currentFile'] = 'n/a' # video
		self.trial['lastStillTime'] = None
		
		self.newEvent('startTrial', self.trialNum, now)
		# trials always start with an epoch
		#self.newEpoch(now)
		
	def stopTrial(self):
		# todo: finish up and close trial file
		now = time.time()
		if self.isRunning:
			logger.debug('stopTrial')
			self.newEvent('stopTrial', self.trialNum, now)
			self.trial['isRunning'] = False
			self.saveTrial()
		
	def newEvent(self, type, val, now=time.time()):
		if self.isRunning:
			self.trial['eventTypes'].append(type)
			self.trial['eventValues'].append(val)
			self.trial['eventTimes'].append(now)
		
	def newEpoch(self, now=time.time()):
		if self.isRunning:
			self.trial['currentEpoch'] += 1
			self.trial['lastEpochSeconds'] = now
			self.newEvent('newRepeat', self.currentEpoch, now=now)
		
	def getFilename(self, withRepeat=False):
		'''
		Get a base filename from trial
		Caller isresponsible for appending proper filetype extension
		'''
		hostnameID_str = ''
		if self.trial['hostnameID']:
			hostnameID_str = '_' + self.trial['hostnameID']
		animalID_str = ''
		if self.trial['animalID']:
			animalID_str = '_id' + self.trial['animalID']
		conditionID_str = ''
		if self.trial['conditionID']:
			conditionID_str = '_c' + self.trial['conditionID']
		# file names will always have (hostname, animal, condition, trial)
		filename = self.trial['startTimeStr'] + hostnameID_str + animalID_str + conditionID_str + '_t' + str(self.trialNum)
		if withRepeat:
			filename += '_r' + str(self.currentEpoch)
		return filename
		
	def saveTrial(self):
		delim = ','
		eol = '\n'
		saveFile = self.getFilename() + '.txt'
		savePath = os.path.join('/home/pi/video', self.trial['dateStr'])
		saveFilePath = os.path.join(savePath, saveFile)
		if not os.path.exists(savePath):
			os.makedirs(savePath)
		dateStr = self.trial['dateStr']
		timeStr = self.trial['timeStr']
		fakeNow = ''
		with open(saveFilePath, 'w') as file:
			# one line header
			headerLine = 'date=' + self.trial['dateStr'] + ';' \
							'time=' + self.trial['timeStr'] + ';' \
							'startTimeSeconds=' + str(self.trial['startTimeSeconds']) + ';' \
							'hostname=' + self.trial['hostnameID'] + ';' \
							'id=' + self.trial['animalID'] + ';' \
							'condition=' + self.trial['conditionID'] + ';' \
							'trialNum=' + str(self.trial['trialNum']) + ';' \
							'numRepeats=' + str(self.trial['currentEpoch']) + eol
			file.write(headerLine)
			# column header for event data
			columnHeader = 'date' + delim + 'time' + delim + 'seconds' + delim + 'event' + delim + 'value' + eol
			file.write(columnHeader)
			# one line per event
			for idx, eventTime in enumerate(self.trial['eventTimes']):
				# convert epoch seconds to date/time str 
				dateStr = time.strftime('%Y%m%d', time.localtime(eventTime))
				timeStr = time.strftime('%H:%M:%S', time.localtime(eventTime))
				# need the plus at end of each line here
				frameLine = dateStr + delim + \
							timeStr + delim + \
							str(eventTime) + delim + \
							self.trial['eventTypes'][idx] + delim + \
							str(self.trial['eventValues'][idx]) + eol
				file.write(frameLine)

	@property
	def isRunning(self):
		return self.trial['isRunning']

	@property
	def timeElapsed(self):
		''' time elapsed since startTimeSeconds '''
		if self.isRunning:
			return round(time.time() - self.trial['startTimeSeconds'], 2)
		else:
			return None
	
	@property
	def epochTimeElapsed(self):
		if self.isRunning:
			return round(time.time() - self.trial['lastEpochSeconds'], 2)
		else:
			return None
			
	@property
	def numFrames(self):
		return self.trial['eventTypes'].count('frame')

	@property
	def currentEpoch(self):
		#return self.trial['eventTypes'].count('epoch')
		return self.trial['currentEpoch']
		
	@property
	def startTimeSeconds(self):
		return self.trial['startTimeSeconds'] # can be None

	@property
	def hostnameID(self):
		return self.trial['hostnameID'] # can be None

	@property
	def animalID(self):
		return self.trial['animalID'] # can be None

	@property
	def conditionID(self):
		return self.trial['conditionID'] # can be None

if __name__ == '__main__':
	logger = logging.getLogger()
	handler = logging.StreamHandler()
	formatter = logging.Formatter(
			'%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

		
