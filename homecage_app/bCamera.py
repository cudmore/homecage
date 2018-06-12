# Robert H Cudmore
# 20180525

import os, io, time, math, json
from datetime import datetime
import threading
import subprocess

import picamera

import logging
logger = logging.getLogger('flask.app')

class bCamera:
	def __init__(self, trial=None):
		self.camera = None
		self.state = 'idle'
		self.trial = trial # a bTrial class
		
		self.width = 640
		self.height = 480
		self.fps = 30
		
		self.recordDuration = 5 # seconds
		self.recordInfinity = False
		self.numberOfRepeats = 2
		
		self.currentFile = ''
		
		# still image during recording
		self.captureStill = True
		self.stillInterval = 2.0 # seconds
		self.lastStillTime = 0
		self.stillPath = os.path.join(os.path.dirname(__file__), 'static/still.jpg')
		
		self.savePath = '/home/pi/video'
		
		self.converttomp4 = True
		
		self.circulario = None
		self.bufferSeconds = 5 # sec
		
		self.streamWidth = 640
		self.streamHeight = 480
		
		#self.lastResponse = ''
		
	def setConfig(self, config):
		''' this is shitty, set config from original config.json file '''
		self.width = int(config['video']['resolution'].split(',')[0])
		self.height = int(config['video']['resolution'].split(',')[1])
		self.fps = config['video']['fps']

		self.recordDuration = config['video']['fileDuration']
		self.recordInfinity = config['video']['recordInfinity']
		self.numberOfRepeats = config['video']['numberOfRepeats']

		self.captureStill = config['video']['captureStill']
		self.stillInterval = config['video']['stillInterval']
		
		self.converttomp4 = config['video']['converttomp4']

		self.bufferSeconds = config['video']['bufferSeconds']

		self.streamWidth = int(config['video']['streamResolution'].split(',')[0])
		self.streamHeight = int(config['video']['streamResolution'].split(',')[1])
		
	def isState(self, thisState):
		return self.state == thisState
	
	@property
	def lastResponse(self):
		if self.trial:
			return self.trial.lastResponse
		else:
			return 'camera has no trial'
	
	@lastResponse.setter
	def lastResponse(self, str):
		if self.trial:
			self.trial.lastResponse = str
		else:
			print('error: lastResponse.setter did not find trial')
			
	def record(self, onoff):
		okGo = self.state in ['idle'] if onoff else self.state in ['recording']
		logger.debug('record onoff:' + str(onoff) + ' okGo:' + str(okGo))
		if okGo:
			self.state = 'recording' if onoff else 'idle'
			if onoff:
				# start a background thread
				thread = threading.Thread(target=self.recordVideoThread, args=())
				thread.daemon = True							# Daemonize thread
				thread.start()									# Start the execution
			else:
				#self.trial.stopTrial()
				# thread will fall out of loop on self.state=='idle'
				pass
			return onoff
		else:
			return False
				
	def recordVideoThread(self):
		# record individual video files in background thread
		logging.info('recordVideoThread start')
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
		self.camera.led = False
		self.camera.resolution = (self.width, self.height)
		self.camera.framerate = self.fps
		self.camera.start_preview()

		now = time.time()

		# fps, resolution, duration, repeats, recordInfinity
		headerStr = 'video_fps=' + str(self.fps) + ';' \
					'video_resolution=' '"' + str(self.width) + ',' + str(self.height) + '"' + ';' \
					'video_duration=' + str(self.recordDuration) + ';' \
					'video_repeats=' + str(self.numberOfRepeats) + ';' \
					'video.continuous=' + '"' + str(self.recordInfinity) + '"' + ';' \
					
		self.trial.startTrial(headerStr=headerStr)

		startDateStr = time.strftime('%Y%m%d', time.localtime(now)) 

		self.saveVideoPath = os.path.join(self.savePath, startDateStr)
		if not os.path.isdir(self.saveVideoPath):
			os.makedirs(self.saveVideoPath)

		self.lastStillTime = 0 # seconds
		currentRepeat = 1
		numberOfRepeats = float('Inf') if self.recordInfinity else self.numberOfRepeats
		while self.isState('recording') and (currentRepeat <= numberOfRepeats):
			
			self.trial.newEpoch()

			#the file we are about to record/save
			self.currentFile = self.trial.getFilename(withRepeat=True) + '.h264' # time stamp is based on trial.newEpoch()
			videoFilePath = os.path.join(self.saveVideoPath, self.currentFile)
			logger.debug('Start video file:' + videoFilePath + ' dur:' + str(self.recordDuration) + ' fps:' + str(self.fps))
			self.trial.newEvent('recordVideo', currentRepeat, str=videoFilePath)		 # paired with stopVideo	

			startRecordSeconds = time.time()
			try:
				self.camera.start_recording(videoFilePath)
			except (IOError) as e:
				logger.error('start recording:' + str(e))
				self.camera.close()
				self.lastResponse = str(e)
				self.state = 'idle'
				raise
				
			# record until duration or we receive stop signal
			while self.isState('recording') and (time.time() <= (startRecordSeconds + float(self.recordDuration))):
				self.camera.wait_recording()
				if self.captureStill and time.time() > (self.lastStillTime + float(self.stillInterval)):
					self.camera.capture(self.stillPath, use_video_port=True)
					self.lastStillTime = time.time()
					'''
					self.trial['lastStillTime'] = datetime.now().strftime('%Y%m%d %H:%M:%S')
					'''			
			self.camera.stop_recording()

			logger.debug('Stop video file:' + videoFilePath)
			self.trial.newEvent('stopVideo', currentRepeat, str=videoFilePath) # paired with startVideo			

			currentRepeat += 1

			# convert to mp4
			if self.converttomp4:
				self.convertVideo(videoFilePath, self.fps)
			
		self.state = 'idle'
		self.currentFile = ''
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
				cmd = ["./bin/stream", "start", str(self.streamWidth), str(self.streamHeight)]
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
					startTime = datetime.now()
					startTimeStr = startTime.strftime('%Y%m%d')
					saveVideoPath = os.path.join(self.savePath, startTimeStr)
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
		This will record until (i) recordDuration or (ii) stop trigger
		'''
		if 1: #self.camera:
			lastStill = 0
			numberOfRepeats = float('Inf') if self.recordInfinity else self.numberOfRepeats
			
			logger.debug('Initializing camera')
			self.camera = picamera.PiCamera()
			self.camera.resolution = (self.width, self.height)
			self.camera.led = 0
			self.camera.framerate = self.fps
			self.camera.start_preview()

			logger.debug('Starting circular stream, bufferSeconds:' + str(self.bufferSeconds))
			self.circulario = picamera.PiCameraCircularIO(self.camera, seconds=self.bufferSeconds)
			self.camera.start_recording(self.circulario, format='h264')

			while self.isState('armed') or self.isState('armedrecording'):
				self.camera.wait_recording()
				#if self.isState('armedrecording') and (currentRepeat <= numberOfRepeats):
				if self.isState('armedrecording'):
					currentRepeat = 1 #important: for now we will just do one repeat
					
					#todo: log time when trigger in is received
					now = time.time()
					startTimeStr = time.strftime('%Y%m%d_%H%M%S', time.localtime(now)) 
					
					#self.lastResponse = 'Trigger in at'
					
					self.trial.startTrial(now=now)

					beforefilename = startTimeStr + '_before_t' + str(self.trial.trialNum) + '.h264'
					afterfilename = startTimeStr + '_after_t' + str(self.trial.trialNum) + '.h264'
					beforefilepath = os.path.join(saveVideoPath, beforefilename)
					afterfilepath = os.path.join(saveVideoPath, afterfilename)

					self.trial.newEpoch(now)
					self.trial.newEvent('beforefilepath', currentRepeat, str=beforefilepath, now=now)
					self.trial.newEvent('afterfilepath', currentRepeat, str=afterfilepath, now=now)

					#currentRepeat = 1

					# As soon as we detect motion, split the recording to
					# record the frames "after" motion
					self.camera.split_recording(afterfilepath)					
					# Write the 10 seconds "before" motion to disk as well
					self.circulario.copy_to(beforefilepath, seconds=self.bufferSeconds)
					self.circulario.clear()
				
					logger.debug('Start video file:' + afterfilename)
					self.currentFile = afterfilename
				
					# for now, record ONE video file per start trigger
					recordDuration = self.recordDuration
					stopOnTrigger = False #todo: make this global and set on pin
					while self.isState('armedrecording') and not stopOnTrigger and (time.time()<(now + float(recordDuration))):
						self.camera.wait_recording() # seconds

						if self.captureStill and time.time() > (lastStill + float(self.stillInterval)):
							self.camera.capture(self.stillPath, use_video_port=True)
							lastStill = time.time()
						
					self.camera.split_recording(self.circulario)
					#currentRepeat += 1
			
					self.currentFile = ''
					self.trial.stopTrial()

					self.state = 'armed'
					self.lastResponse = 'Stopped trial at xxx'
										
					# convert to mp4
					if self.converttomp4:
						# before
						self.convertVideo(beforefilepath, self.fps)
						# after
						self.convertVideo(afterfilepath, self.fps)

	'''
	#called from armVideoThread()
	def write_video_(self, stream, beforeFilePath):
		# Write the entire content of the circular buffer to disk. No need to
		# lock the stream here as we're definitely not writing to it simultaneously
		with io.open(beforeFilePath, 'wb') as output:
			for frame in stream.frames:
				if frame.frame_type == picamera.PiVideoFrameType.sps_header:
					stream.seek(frame.position)
					break
			while True:
				buf = stream.read1()
				if not buf:
					break
				output.write(buf)
		# Wipe the circular stream once we're done
		stream.seek(0)
		stream.truncate()
	'''
	
	def annotate(self, text):
		''' add watermark to video '''
		try:
			self.camera.annotate_background = picamera.Color('black')
			self.camera.annotate_text = str(text)
		except picamera.exc.PiCameraClosed as e:
			print(e)

	def convertVideo(self, videoFilePath, fps):
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
	