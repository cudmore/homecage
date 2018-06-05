# 20180524
# we can not create camera with picamera.PiCamera() AND then stream
# todo: write camera class to make sure we follow this logic

import picamera

camera = None

try:
	camera = picamera.PiCamera()
except picamera.exc.PiCameraMMALError:
	print 'error 1: not initialized'
	
print 'camera:', camera

if camera is not None:
	width = 640
	height = 480
	camera.resolution = (width, height)
	camera.led = 0
	camera.framerate = 30
	camera.start_preview()
else:
	pass
	
if camera:
	try:
		camera.stop_recording()	
	except picamera.exc.PiCameraNotRecording:
		print 'error 2: not recording'
else:
	pass
	
if camera:
	camera.close()

print 'camera:', camera

if (__name__ == '__main__'):
	while True:
		pass