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
		self.trial['eventStrings'] = []
		self.trial['eventTimes'] = [] # relative to self.trial['startTimeSeconds']

		self.trial['currentFile'] = ''
		self.trial['lastStillTime'] = None

		self.trial['hostnameID'] = ''
		self.trial['animalID'] = ''
		self.trial['conditionID'] = ''
		
		self.trial['headerStr'] = ''
		
	def setHostname(self, hostnameID):
		self.trial['hostnameID'] = hostnameID
		
	def setAnimalID(self, animalID):
		self.trial['animalID'] = animalID
		
	def setConditionID(self, conditionID):
		self.trial['conditionID'] = conditionID
		
	def startTrial(self, headerStr='', now=None):
		if now is None:
			now = time.time()
			
		self.trialNum += 1
		
		self.trial['headerStr'] = headerStr

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
		self.trial['eventStrings'] = []
		self.trial['eventTimes'] = [] # relative to self.trial['startTimeSeconds']
		
		self.trial['currentFile'] = 'n/a' # video
		self.trial['lastStillTime'] = None
		
		logger.debug('startTrial')
		self.newEvent('startTrial', self.trialNum, now=now)
		# trials always start with an epoch
		#self.newEpoch(now)
		
	def stopTrial(self):
		# todo: finish up and close trial file
		now = time.time()
		if self.isRunning:
			logger.debug('stopTrial')
			self.newEvent('stopTrial', self.trialNum, now=now)
			self.trial['isRunning'] = False
			self.saveTrial()
		
	def newEvent(self, type, val, str='', now=None):
		if now is None:
			now = time.time()
		if self.isRunning:
			self.trial['eventTypes'].append(type)
			self.trial['eventValues'].append(val)
			self.trial['eventStrings'].append(str)
			self.trial['eventTimes'].append(now)
		
	def newEpoch(self, now=None):
		if now is None:
			now = time.time()
		if self.isRunning:
			self.trial['currentEpoch'] += 1
			self.trial['lastEpochSeconds'] = now
			self.newEvent('newRepeat', self.currentEpoch, now=now)
			print('newEpoch:', self.trial['currentEpoch'], self.trial['lastEpochSeconds'])
		
	def getFilename(self, useStartTime=False, withRepeat=False):
		'''
		Get a base filename from trial
		Caller isresponsible for appending proper filetype extension
		'''
		hostnameID_str = ''
		if self.trial['hostnameID']:
			hostnameID_str = '_' + self.trial['hostnameID']
		animalID_str = ''
		if self.trial['animalID']:
			animalID_str = '_' + self.trial['animalID']
		conditionID_str = ''
		if self.trial['conditionID']:
			conditionID_str = '_' + self.trial['conditionID']
		# time is the time the epoch was started
		if useStartTime:
			useThisTime = time.localtime(self.trial['startTimeSeconds'])
		else:
			useThisTime = time.localtime(self.trial['lastEpochSeconds'])
		timeStr = time.strftime('%Y%m%d_%H%M%S', useThisTime) 
		
		# file names will always have (hostname, animal, condition, trial)
		filename = timeStr + hostnameID_str + animalID_str + conditionID_str + '_t' + str(self.trialNum)
		if withRepeat:
			filename += '_r' + str(self.currentEpoch)
		return filename
		
	def saveTrial(self):
		delim = ','
		eol = '\n'
		saveFile = self.getFilename(useStartTime=True) + '.txt'
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
							'hostname=' + '"' + self.trial['hostnameID'] + '"' + ';' \
							'id=' + '"' + self.trial['animalID'] + '"' + ';' \
							'condition=' + '"' + self.trial['conditionID'] + '"' + ';' \
							'trialNum=' + str(self.trial['trialNum']) + ';' \
							'numRepeats=' + str(self.trial['currentEpoch']) + ';'
			if self.trial['headerStr']:
				headerLine += self.trial['headerStr']
			headerLine += eol
			
			file.write(headerLine)
			# column header for event data is (date, time, sconds, event, value, str
			columnHeader = 'date' + delim + 'time' + delim + 'seconds' + delim + 'event' + delim + 'value' +  +delim + 'str' + eol
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
							str(self.trial['eventValues'][idx]) + delim + \
							self.trial['eventStrings'][idx]
				frameLine += eol
				file.write(frameLine)

	def loadTrialFile(Self, path):
		'''
		load a .txt trial file
		'''
		ret = OrderedDict()
		ret['recordVideo'] = []
		if not os.path.isfile(path):
			return ret
		with open(path) as f:
			# parse one line header
			header = f.readline().strip()
			print('header 0:', header)
			if header.endswith(';'):
				# print('stripping ; from header', str(len(header)))
				header = header[0:len(header)-1] # python string index uses ':' and not ','
			print('header 1:', header)
			header = header.split(';') # header is a list of k=v
			# print('loadTrialFile() header:', header)
			for item in header:
				lhs,rhs = item.split('=')
				ret[lhs] = rhs
				
			# one line column names
			# todo: parse column names so we don't need to use [idx] below
			columnNames = f.readline().rstrip()
			# list of events, one per line
			event = f.readline().rstrip()
			while event:
				# print('   event:', event)
				event = event.split(',') # event is a list
				for item in event:
					# something like: 20180611,09:03:16,1528722196.370188,recordVideo,/home/pi/video/20180611/20180611_090316_hc1_animal_condition_t1_r2.h264
					itemType = item[3]
					if itemType == 'recordVideo':
						recordVideo = {}
						recordVideo['repeat'] = item[4]
						recordVideo['videoFile'] = item[5]
						ret['recordVideo'].append(recordVideo)
				event = f.readline().rstrip()
		return ret
		
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
			return round(time.time() - self.trial['lastEpochSeconds'], 1)
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

		
