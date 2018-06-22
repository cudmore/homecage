# Robert H Cudmore
# 20180525

import os, io, time, math, json
from datetime import datetime
from collections import OrderedDict
import threading, subprocess, queue

import picamera
import bTrial

import logging
logger = logging.getLogger('flask.app')

class bCamera:
	def __init__(self, trial=None):
		self.camera = None

		self.state = 'idle'
		
		if trial is None:
			self.trial = bTrial()
		else:
			self.trial = trial # a bTrial class
		
		self.currentFile = '' # actually part of trial
		self.secondsElapsedStr = ''
		
		# still image during recording
		self.lastStillTime = 0
		self.stillPath = os.path.join(os.path.dirname(__file__), 'static/still.jpg')
		
		self.convertErrorQueue = queue.Queue() # queue is infinite length
		self.convertFileQueue = queue.Queue()
		self.startConvertThread()
		
	def isState(self, thisState):
		return self.state == thisState
	
	@property
	def lastResponse(self):
		self.trial.lastResponse
	
	@lastResponse.setter
	def lastResponse(self, str):
		self.trial.lastResponse = str
			
	def record(self, onoff, startNewTrial=True):
		okGo = self.state in ['idle'] if onoff else self.state in ['recording']
		logger.debug('record onoff:' + str(onoff) + ' okGo:' + str(okGo))
		if okGo:
			self.state = 'recording' if onoff else 'idle'
			if onoff:
				# start a background thread
				thread = threading.Thread(target=self.recordVideoThread, args=(startNewTrial,))
				thread.daemon = True							# Daemonize thread
				thread.start()									# Start the execution
			else:
				#self.trial.stopTrial()
				# thread will fall out of loop on self.state=='idle'
				pass
			return onoff
		else:
			return False
				
	def initCamera(self):
		ret = OrderedDict()
		
		try:
			self.camera = picamera.PiCamera()
		except (picamera.exc.PiCameraMMALError) as e:
			logger.error('picamera PiCameraMMALError: ' + str(e))
			self.lastResponse = str(e)
			self.state = 'idle'
			raise
		except (picamera.exc.PiCameraError) as e:
			logger.error('picamera PiCameraError: ' + str(e))
			self.lastResponse = str(e)
			self.state = 'idle'
			raise

		ret['led'] = self.trial.getConfig('video', 'led')
		#print("ret['led']:", ret['led'])
		self.camera.led = ret['led']

		resolution = self.trial.getConfig('video', 'resolution')
		width = int(resolution.split(',')[0])
		height = int(resolution.split(',')[1])
		self.camera.resolution = (width, height)
		
		ret['fps'] = self.trial.getConfig('video', 'fps')
		self.camera.framerate = ret['fps']
		
		# package trial config into a struct
		ret['repeatDuration'] = self.trial.getConfig('trial', 'repeatDuration') # different key names
		ret['repeatInfinity'] = self.trial.getConfig('trial', 'repeatInfinity')
		ret['numberOfRepeats'] = self.trial.getConfig('trial', 'numberOfRepeats')
		ret['savePath'] = self.trial.getConfig('trial', 'savePath')
		
		ret['captureStill'] = self.trial.getConfig('video', 'captureStill')
		ret['stillInterval'] = self.trial.getConfig('video', 'stillInterval')
		ret['converttomp4'] = self.trial.getConfig('video', 'converttomp4')
		ret['bufferSeconds'] = self.trial.getConfig('video', 'bufferSeconds')

		return ret
		
	def recordVideoThread(self, startNewTrial=True):
		# record individual video files in background thread
		logging.info('recordVideoThread start')
		
		#
		# grab configuration from trial
		thisCamera = self.initCamera()
		repeatDuration = thisCamera['repeatDuration']
		repeatInfinity = thisCamera['repeatInfinity']
		numberOfRepeats = thisCamera['numberOfRepeats']
		fps = thisCamera['fps']
		captureStill = thisCamera['captureStill']
		stillInterval = thisCamera['stillInterval']
		converttomp4 = thisCamera['converttomp4']
		savePath = thisCamera['savePath']
		# tweek numberOfRepeats
		numberOfRepeats = float('Inf') if repeatInfinity else float(numberOfRepeats)
		
		#
		self.camera.start_preview()

		now = time.time()

		if startNewTrial:
			self.trial.startTrial()
		
		startDateStr = time.strftime('%Y%m%d', time.localtime(now)) 
		saveVideoPath = os.path.join(savePath, startDateStr)
		if not os.path.isdir(saveVideoPath):
			os.makedirs(saveVideoPath)

		self.lastStillTime = 0 # seconds
		currentRepeat = 1
		while self.isState('recording') and (currentRepeat <= numberOfRepeats):
			
			self.trial.newEpoch()

			#the file we are about to record/save
			self.currentFile = self.trial.getFilename(withRepeat=True) + '.h264' # time stamp is based on trial.newEpoch()
			self.secondsElapsedStr = '0'
			videoFilePath = os.path.join(saveVideoPath, self.currentFile)
			logger.debug('Start video file:' + videoFilePath + ' dur:' + str(repeatDuration) + ' fps:' + str(fps))
			self.trial.newEvent('recordVideo', currentRepeat, str=videoFilePath)		 # paired with stopVideo	

			try:
				self.camera.start_recording(videoFilePath)
				self.lastResponse = 'camera recording file ' + self.currentFile
			except (IOError) as e:
				logger.error('start recording:' + str(e))
				self.camera.close()
				self.lastResponse = str(e)
				self.state = 'idle'
				raise

			startRecordSeconds = time.time()
				
			# record until duration or we receive stop signal
			while self.isState('recording') and (time.time() <= (startRecordSeconds + float(repeatDuration))):
				self.camera.wait_recording()
				if captureStill and time.time() > (self.lastStillTime + float(stillInterval)):
					self.camera.capture(self.stillPath, use_video_port=True)
					self.lastStillTime = time.time()
					'''
					self.trial['lastStillTime'] = datetime.now().strftime('%Y%m%d %H:%M:%S')
					'''
				self.secondsElapsedStr = str(round(time.time() - startRecordSeconds, 1))
					
			self.camera.stop_recording()

			logger.debug('Stop video file:' + videoFilePath)
			self.trial.newEvent('stopVideo', currentRepeat, str=videoFilePath) # paired with startVideo			
			
			currentRepeat += 1

			# convert to mp4
			if converttomp4:
				self.convertVideo(videoFilePath, fps)

		self.lastResponse = 'camera stopped'
			
		self.state = 'idle'
		self.currentFile = ''
		self.secondsElapsedStr = 'n/a'
		
		self.trial.stopTrial()
		self.camera.close()
		logging.debug('recordVideoThread end')

	def stream(self,onoff):
		''' start and stop video stream '''
		okGo = self.state in ['idle'] if onoff else self.state in ['streaming']
		logger.debug('stream onoff:' + str(onoff) + ' okGo:' + str(okGo))

		if okGo:
			self.state = 'streaming' if onoff else 'idle'
			if onoff:
				streamResolution = self.trial.getConfig('video', 'streamResolution')
				streamWidth = streamResolution.split(',')[0] #str is ok here
				streamHeight = streamResolution.split(',')[1]
				cmd = ["./bin/stream", "start", str(streamWidth), str(streamHeight)]
				logger.info(cmd)
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
					self.lastResponse = 'Streaming is on'
				except subprocess.CalledProcessError as e:
					error = e.output.decode('utf-8')
					logger.error('stream on exception: ' + error)
					self.lastResponse = error
					#self.stream(False)
					self.state = 'idle'
					raise
			else:
				cmd = ["./bin/stream", "stop"]
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
					self.lastResponse = 'Streaming is off'
				except subprocess.CalledProcessError as e:
					error = e.output.decode('utf-8')
					logger.error('stream off exception: ' + error)
					self.lastResponse = error
					raise
			
	def arm(self, onoff):
		''' start and stop arm '''
		okGo = self.state in ['idle'] if onoff else self.state in ['armed']
		logger.debug('arm onoff:' + str(onoff) + ' okGo:' + str(okGo))
		if okGo:
			self.state = 'armed' if onoff else 'idle'
			if onoff:
				# spawn background task with video loop
				#try:
				if 1:

					# save into date folder
					savePath = self.trial.getConfig('trial', 'savePath')
					startTime = datetime.now()
					startTimeStr = startTime.strftime('%Y%m%d')
					saveVideoPath = os.path.join(savePath, startTimeStr)
					if not os.path.isdir(saveVideoPath):
						os.makedirs(saveVideoPath)

					thread = threading.Thread(target=self.armVideoThread, args=([saveVideoPath]))
					thread.daemon = True							# Daemonize thread
					thread.start()									# Start the execution

					self.lastResponse = 'Armed and waiting for trigger'
			else:
				if self.camera:
					# stop background task with video loop
					try:
						self.camera.stop_recording()	
						self.camera.close()
					except picamera.exc.PiCameraNotRecording:
						logger.error('PiCameraNotRecording')
					self.lastResponse = self.state
						
	def startArmVideo(self, now=None):
		if now is None:
			now = time.time()
		if self.isState('armed'):
			logger.debug('startArmVideo()')
			self.state = 'armedrecording'
			self.lastResponse = 'Trigger in at ' + time.strftime('%H:%M:%s', time.localtime(now)) 
			
	def stopArmVideo(self):
		if self.isState('armedrecording'):
			now=time.time()
			logger.debug('stopArmVideo()')
			self.state = 'armed'
			self.lastResponse = 'Stopped armed video recording at ' + time.strftime('%H:%M:%s', time.localtime(now))

	def armVideoThread(self, saveVideoPath):
		'''
		Arm the camera by starting a circular stream
		
		Start recording from circular stream in response to trigger.
		This will record until (i) repeatDuration or (ii) stop trigger
		'''
		if 1: #self.camera:
			lastStill = 0
			
			#
			thisCamera = self.initCamera()
			repeatDuration = thisCamera['repeatDuration']
			repeatInfinity = thisCamera['repeatInfinity']
			numberOfRepeats = thisCamera['numberOfRepeats']
			fps = thisCamera['fps']
			captureStill = thisCamera['captureStill']
			stillInterval = thisCamera['stillInterval']
			converttomp4 = thisCamera['converttomp4']
			savePath = thisCamera['savePath']
			bufferSeconds = thisCamera['bufferSeconds'] # for video loop
			# tweek numberOfRepeats
			#numberOfRepeats = float('Inf') if repeatInfinity else float(numberOfRepeats)
			
			self.camera.start_preview()

			logger.debug('Starting circular stream, bufferSeconds:' + str(bufferSeconds))
			circulario = picamera.PiCameraCircularIO(self.camera, seconds=bufferSeconds)
			self.camera.start_recording(circulario, format='h264')

			while self.isState('armed') or self.isState('armedrecording'):
				self.camera.wait_recording()
				#if self.isState('armedrecording') and (currentRepeat <= numberOfRepeats):
				if self.isState('armedrecording'):
					currentRepeat = 1 #important: for now we will just do one repeat
					
					#todo: log time when trigger in is received
					#now = time.time()
					#startTimeStr = time.strftime('%Y%m%d_%H%M%S', time.localtime(now)) 
					#self.lastResponse = 'Trigger in at'
					
					# when we receive trigger, we need to start trial !!!
					self.trial.startTrial(startArmVideo=True)

					self.trial.newEpoch()

					# todo: get base file name form trial
					filePrefix = self.trial.getFilename(withRepeat=True) # uses ['lastEpochSeconds']
					beforefilename = filePrefix + '_before.h264'
					afterfilename = filePrefix + '_after.h264'					
					beforefilepath = os.path.join(saveVideoPath, beforefilename) # saveVideoPath is param to *this function
					afterfilepath = os.path.join(saveVideoPath, afterfilename)

					self.trial.newEvent('beforefilepath', currentRepeat, str=beforefilepath)
					self.trial.newEvent('afterfilepath', currentRepeat, str=afterfilepath)

					#currentRepeat = 1

					# As soon as we detect motion, split the recording to
					# record the frames "after" motion
					self.camera.split_recording(afterfilepath)					
					# Write the 10 seconds "before" motion to disk as well
					circulario.copy_to(beforefilepath, seconds=bufferSeconds)
					circulario.clear()
			
					startRecordSeconds = time.time()
					self.secondsElapsedStr = '0'
			
					logger.debug('Start video file:' + afterfilename)
					self.currentFile = afterfilename
				
					# for now, record ONE video file per start trigger
					stopOnTrigger = False #todo: make this global and set on pin
					while self.isState('armedrecording') and not stopOnTrigger and (time.time()<(startRecordSeconds + float(repeatDuration))):
						self.camera.wait_recording() # seconds

						self.secondsElapsedStr = str(round(time.time() - startRecordSeconds, 1))

						if captureStill and time.time() > (lastStill + float(stillInterval)):
							self.camera.capture(self.stillPath, use_video_port=True)
							lastStill = time.time()
						
					self.secondsElapsedStr = 'n/a'

					self.camera.split_recording(circulario)
			
					self.currentFile = ''
					self.trial.stopTrial()

					self.state = 'armed'
					self.lastResponse = 'Stopped trial at xxx'
										
					# convert to mp4
					if converttomp4:
						# before
						self.convertVideo(beforefilepath, fps)
						# after
						self.convertVideo(afterfilepath, fps)

	def annotate(self, text):
		''' add watermark to video '''
		if self.camera:
			try:
				self.camera.annotate_background = picamera.Color('black')
				self.camera.annotate_text = str(text)
			except picamera.exc.PiCameraClosed as e:
				logger.error('watermark ' + str(e))

	#########################################################################
	# convert video thread
	#########################################################################
	# convertErrorQueue, convertFileQueue
	def startConvertThread(self):
		""" Call this in constructor """
		#self.convertFileQueue = queue.Queue()
		#self.convertErrorQueue = queue.Queue()
		thread = threading.Thread(target=self.convertVideoThread, args=(self.convertFileQueue,self.convertErrorQueue,))
		thread.daemon = True							# Daemonize thread
		thread.start()									# Start the execution

	def convertVideoThread(self, fileQueue, errorQueue):
		""" A thread that will monitor fileQueue and call ./bin/convert_video.sh to convert .h264 to .mp4 """
		#print('convertVideoThread() fileQueue:', fileQueue)
		#print('convertVideoThread() errorQueue:', errorQueue)
		while True:
			try:
				file = fileQueue.get(block=False, timeout=0)
			except (queue.Empty) as e:
				pass
			else:
				#print('queue not empty')
				logger.info('starting convertVideoThread:' + file['path'] + ' fps:' + str(file['fps']))
				cmd = ["./bin/convert_video.sh", file['path'], str(file['fps']), "delete"]
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
					#self.lastResponse = 'Converted video to mp4'
				except (subprocess.CalledProcessError, OSError) as e:
					logger.error('convertVideoThread ./bin/convert_video exception: ' + str(e))
					pass
				except:
					raise	
				logger.info('finished convertVideoThread:' + file['path'] + ' fps:' + str(file['fps']))
				
			time.sleep(1)
	
	def convertVideo(self, videoFilePath, fps):
		"""
		Add a file/fps to the convertFile queue. convertVideoThread() will process it
		"""
		theDict = {}
		theDict['path'] = videoFilePath
		theDict['fps'] = fps
		#print('convertVideo adding to file queue:', theDict)
		self.convertFileQueue.put(theDict)
		
		'''
		this was working
		# at end of video recording, convert h264 to mp4
		logger.debug('converting video:' + videoFilePath + ' fps:' + str(fps))
		cmd = ["./bin/convert_video.sh", videoFilePath, str(fps)]
		try:
			out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
			self.lastResponse = 'Converted video to mp4'
		except (subprocess.CalledProcessError, OSError) as e:
			#print('e:', e)
			#print('e.returncode:', e.returncode) # 1 is failure, 0 is sucess
			#print('e.output:', e.output)
			logger.error('bin/convert_video exception: ' + str(e))
			pass
		except:
			raise	
		logger.debug('converting video finished')
		'''
			
if __name__ == '__main__':
	logger = logging.getLogger()
	handler = logging.StreamHandler()
	formatter = logging.Formatter(
			'%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)
	logger.setLevel(logging.DEBUG)

	from bTrial import bTrial
	t = bTrial()
	
	c = bCamera(trial=t)

	'''
	# test recording
	c.state = 'recording'
	c.recordVideoThread()
	'''
	
	'''
	# test streaming
	c.state = 'idle'
	c.stream(1)
	time.sleep(20)
	c.stream(0)
	'''
	
	# armed recording
	c.arm(True)
	c.startArmVideo()
	time.sleep(20)
	c.stopArmVideo()
	