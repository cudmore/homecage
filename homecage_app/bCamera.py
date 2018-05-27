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
		self.stillInterval = 2 # seconds
		self.lastStillTime = 0
		self.stillPath = os.path.join(os.path.dirname(__file__), 'static/still.jpg')
		
		self.savePath = '/home/pi/video'
		
		self.converttomp4 = True
		
		self.circulario = None
		self.bufferSeconds = 5 # sec
		
		self.streamWidth = 640
		self.streamHeight = 480
		
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
		
	def record(self, onoff):
		okGo = self.state in ['idle'] if onoff else self.state in ['recording']
		logger.debug('record onoff:' + str(onoff) + ' okGo:' + str(okGo))
		if okGo:
			self.state = 'recording' if onoff else 'idle'
			if onoff:
				# set output path
				now = time.time()
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d')
				self.saveVideoPath = os.path.join(self.savePath, startTimeStr)
				if not os.path.isdir(self.saveVideoPath):
					os.makedirs(self.saveVideoPath)

				if self.trial is not None:
					self.trial.startTrial(now=now)
								
				# start a background thread
				thread = threading.Thread(target=self.recordVideoThread, args=())
				thread.daemon = True							# Daemonize thread
				thread.start()									# Start the execution
			else:
				if self.trial is not None:
					self.trial.stopTrial()
			return onoff
		else:
			return False
				
	def recordVideoThread(self):
		# record individual video files in background thread
		logging.info('recordVideoThread start')
		self.camera = picamera.PiCamera()
		self.camera.led = False
		self.camera.resolution = (self.width, self.height)
		self.camera.framerate = self.fps
		self.camera.start_preview()

		self.lastStillTime = 0 # seconds
		currentRepeat = 1
		numberOfRepeats = float('Inf') if self.recordInfinity else self.numberOfRepeats
		while self.isState('recording') and (currentRepeat <= numberOfRepeats):
			now = time.time()
			startTime = datetime.now()
			startTimeStr = startTime.strftime('%Y%m%d_%H%M%S')

			#the file we are about to record/save
			self.currentFile = startTimeStr + '.h264'
			
			# save into date folder
			dateStr = startTime.strftime('%Y%m%d')
			saveVideoPath = os.path.join(self.savePath, dateStr)
			if not os.path.isdir(saveVideoPath):
				os.makedirs(saveVideoPath)

			videoFilePath = os.path.join(saveVideoPath, self.currentFile)
			logger.debug('Start video file:' + videoFilePath + ' dur:' + str(self.recordDuration) + ' fps:' + str(self.fps))

			if self.trial is not None:
				self.trial.newEpoch(now)
				self.trial.newEvent('recordVideo', videoFilePath, now=now)			

			self.camera.start_recording(videoFilePath)
			while self.isState('recording') and (time.time() < (now + self.recordDuration)):
				self.camera.wait_recording(0.3)
				if self.captureStill and time.time() > (self.lastStillTime + self.stillInterval):
					self.camera.capture(self.stillPath, use_video_port=True)
					self.lastStillTime = time.time()
					'''
					self.trial['lastStillTime'] = datetime.now().strftime('%Y%m%d %H:%M:%S')
					'''
			self.camera.stop_recording()
			currentRepeat += 1

			# convert to mp4
			if self.converttomp4:
				self.convertVideo(videoFilePath, self.fps)
			
		self.state = 'idle'
		self.currentFile = ''
		if self.trial is not None:
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
				cmd = ["./stream", "start", str(self.streamWidth), str(self.streamHeight)]
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
					self.lastResponse = 'Streaming is on'
				except subprocess.CalledProcessError as e:
				    print('e:', e)
				    print('e.returncode:', e.returncode) # 1 is failure, 0 is sucess
				    print('e.output:', e.output)
			else:
				cmd = ["./stream", "stop"]
				try:
					out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
				except subprocess.CalledProcessError as e:
				    print('e:', e)
				    print('e.returncode:', e.returncode) # 1 is failure, 0 is sucess
				    print('e.output:', e.output)
			
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
					logger.debug('Initializing camera')
					self.camera = picamera.PiCamera()
					self.camera.resolution = (self.width, self.height)
					self.camera.led = 0
					self.camera.framerate = self.fps
					self.camera.start_preview()

					logger.debug('Starting circular stream')
					self.circulario = picamera.PiCameraCircularIO(self.camera, self.bufferSeconds)
					self.camera.start_recording(self.circulario, format='h264')				
			else:
				if self.camera:
					# stop background task with video loop
					try:
						self.camera.stop_recording()	
						self.camera.close()
					except picamera.exc.PiCameraNotRecording:
						logger.error('PiCameraNotRecording')
						
	def startArmVideo(self, now=time.time()):
		if self.isState('armed'):
			logger.debug('startArmVideo()')
			self.state = 'armedrecording'
			if self.trial is not None:
				self.trial.startTrial(now=now)
			# start a background thread
			thread = threading.Thread(target=self.armVideoThread, args=())
			thread.daemon = True							# Daemonize thread
			thread.start()									# Start the execution

	def stopArmVideo(self):
		if self.isState('armedrecording'):
			logger.debug('stopArmVideo()')
			# force armVideoThread() out of while loop
			if self.trial is not None:
				self.trial.stopTrial()
			self.state = 'armed'

	def armVideoThread(self):
		'''
		Start recording from circular stream in response to trigger.
		This will record until (i) recordDuration or (ii) stop trigger
		'''
		if self.camera:
			lastStill = 0
			#stillPath = os.path.dirname(__file__) + 'still.jpg'
			currentRepeat = 1
			numberOfRepeats = float('Inf') if self.recordInfinity else self.numberOfRepeats
			while self.isState('armedrecording') and (currentRepeat <= numberOfRepeats):
				#todo: log time when trigger in is received
				now = time.time()
				startTime = datetime.now()
				startTimeStr = startTime.strftime('%Y%m%d_%H%M%S')
				beforefilename = startTimeStr + '_before' + '.h264'
				afterfilename = startTimeStr + '_after' + '.h264'

				# save into date folder
				startTimeStr = startTime.strftime('%Y%m%d')
				saveVideoPath = os.path.join(self.savePath, startTimeStr)
				if not os.path.isdir(saveVideoPath):
					os.makedirs(saveVideoPath)

				beforefilepath = os.path.join(saveVideoPath, beforefilename)
				afterfilepath = os.path.join(saveVideoPath, afterfilename)
				try:
					self.camera.split_recording(afterfilepath)
				except picamera.exc.PiCameraNotRecording:
					logger.error('PiCameraNotRecording outer loop')
				
				if self.trial is not None:
					self.trial.newEpoch(now)
					self.trial.newEvent('recordArmVideo', afterfilepath, now=now)

				logger.debug('Start video file:' + beforefilepath)
				self.currentFile = afterfilename
				
				# Write the 10 seconds "before" motion to disk as well
				self.write_video_(self.circulario, beforefilepath)

				recordDuration = self.recordDuration
				stopOnTrigger = 0 #todo: make this global and set on pin
				while self.isState('armedrecording') and not stopOnTrigger and (time.time()<(now + recordDuration)):
					try:
						self.camera.wait_recording(1) # seconds
					except picamera.exc.PiCameraNotRecording:
						logger.error('PiCameraNotRecording inner loop')

					if self.captureStill and time.time() > (lastStill + self.stillInterval):
						self.camera.capture(self.stillPath, use_video_port=True)
						lastStill = time.time()
						
				self.camera.split_recording(self.circulario)
				currentRepeat += 1
				
				# convert to mp4
				if self.converttomp4:
					# before
					self.convertVideo(beforefilepath, self.fps)
					# after
					self.convertVideo(afterfilepath, self.fps)

				time.sleep(0.005) # seconds
			self.state = 'armed'
			self.currentFile = ''
			if self.trial is not None:
				self.trial.stopTrial()
			'''
			if self.camera:
				self.camera.stop_recording()	
				self.camera.close()
			'''
		time.sleep(0.05)

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
		cmd = ["./convert_video.sh", videoFilePath, str(fps)]
		try:
			out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
			self.lastResponse = 'Converted video to mp4'
		except subprocess.CalledProcessError as e:
			print('e:', e)
			print('e.returncode:', e.returncode) # 1 is failure, 0 is sucess
			print('e.output:', e.output)
			self.lastResponse = e.output

		# append to dict and save in file
		dirname = os.path.dirname(videoFilePath) 
		mp4File = os.path.basename(videoFilePath).split('.')[0] + '.mp4'
		mp4Path = os.path.join(dirname, mp4File)
		#print('mp4Path:', mp4Path)
		#todo: also include .h264 (if we are not converting to .mp4)
		command = "avprobe -show_format -show_streams -loglevel 'quiet' " + str(mp4Path) + ' -of json'
		#command = "avprobe -show_format -show_streams " + str(mp4Path) + ' -of json'
		#print(command)
		child = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
		data, err = child.communicate()
		data = data.decode('utf-8') # python 3
		data = json.loads((data))
		#print data
		fd = {}
		fd['path'] = mp4Path
		fd['file'] = mp4File
		if 'format' in data:
			fd['duration'] =  math.floor(float(data['format']['duration'])*100)/100
		else:
			fd['duration'] =  '?'
		if 'streams' in data:
			fd['width'] =  data['streams'][0]['width']
			fd['height'] =  data['streams'][0]['height']
			#stretch
			#fd['fps'] = data['streams'][0]['avg_frame_rate'].split('/')[0] # parsing 25/1
			#jessie
			#fd['fps'] = data['streams'][0]['r_frame_rate'].split('/')[0] # parsing 25/1
			fd['fps'] = fps
		else:
			fd['width'] =  '?'
			fd['height'] =  '?'
			fd['fps'] = '?'
		
		# load existing database (list of dict)
		folder = os.path.dirname(videoFilePath)
		dbFile = os.path.join(folder,'db.txt')
		#print('dbFile:', dbFile)
		db = []
		if os.path.isfile(dbFile):
			db = json.load(open(dbFile))
			#print 'loaded db:', db
		# append
		db.append(fd)
		# save
		txt = json.dumps(db)
		f = open(dbFile,"w")
		f.write(txt)
		f.close()

			
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
	