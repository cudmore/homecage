import os
import numpy as np
import cv2

videoPath = '/Volumes/pi3/video/20180415/20180415_153113.mp4'
notesPath = '/Volumes/pi3/video/20180415/20180415_153113.txt'

cv2.namedWindow('videowindow')

cap = cv2.VideoCapture(videoPath)

width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = cap.get(cv2.CAP_PROP_FPS)
nFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
nFrames = int(nFrames)

print(width,height,fps,nFrames)

# frame slider
def nothing(x):
	pass

global currentFrame
currentFrame = 0
global frame
frame = None
global currentBrightness
currentBrightness = 0
global milliseconds
milliseconds = None

def adjustBrightness():
	# adjust contrast
	global currentBrightness
	if currentBrightness > 0:
		global frame
		hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
		hsv[:,:,2] += currentBrightness
		frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
	
# work fine
#def onMouse(event, x, y, flags, userdata):
#	print('onMouse()', event, x, y, flags, userdata)

def onTrackbar(frameNumber):
	cap.set(cv2.CAP_PROP_POS_FRAMES, frameNumber)
	global frame
	ret, frame = cap.read()
	global milliseconds
	milliseconds = round(cap.get(cv2.CAP_PROP_POS_MSEC),2)
	adjustBrightness()
	#cv2.imshow('videowindow',frame)
	global currentFrame
	currentFrame = frameNumber
	#print('onTrackbar()', frameNumber, milliseconds)
	
cv2.createTrackbar('Frames','videowindow', 0, int(nFrames)-1, onTrackbar)
cv2.setTrackbarPos('Frames','videowindow',0)

def onBrightness(brightness):
	global currentBrightness
	currentBrightness = brightness
	adjustBrightness()
	
cv2.createTrackbar('Brightness','videowindow', 0, 255, onBrightness)
cv2.setTrackbarPos('Brightness','videowindow',0)

#cv2.setMouseCallback( "videowindow", onMouse, 0 );

play = False
step = 30

# read the first frame
ret, frame = cap.read()
adjustBrightness()
milliseconds = round(cap.get(cv2.CAP_PROP_POS_MSEC),2)

annotationKeys = ['0', '1', '2', '3', '4', '5']

while(cap.isOpened()):

	#gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

	cv2.imshow('videowindow',frame)

	cv2.setTrackbarPos('Frames','videowindow',currentFrame)

	key = cv2.waitKey(2) & 0xff
	if key == ord('q'):
		break
	if key == ord('p') or key == ord(' '):
		play = not play
		print('play' if play else 'pause')
	if key == 2: # left arrow
		currentFrame -= step
		if currentFrame<0:
			currentFrame = 0
		#print('left currentFrame:', currentFrame)
		onTrackbar(currentFrame)
	if key == 3: # right arrow
		currentFrame += step
		if currentFrame>nFrames-1:
			currentFrame = nFrames-2
		#print('right currentFrame:', currentFrame)
		onTrackbar(currentFrame)
	# annotations
	if key == ord('1'):
		#print('behavior 1 at frame', currentFrame, 'milliseconds', milliseconds)
		headerLine = 'file,frame,milliseconds,event' + '\n'
		# make file
		if not os.path.exists(notesPath):
			with open(notesPath,'a') as notesFile:
				notesFile.write(headerLine)
		# append
		noteLine = videoPath + ',' + str(currentFrame) + "," + str(milliseconds) + ',' + '1' + '\n'
		with open(notesPath,'a') as notesFile:
			notesFile.write(noteLine)
		print('file:', notesPath)
		print('   ', headerLine)
		print('   ',noteLine)
	if chr(key) in annotationKeys:
		print('add annotation:', chr(key))
		
	#print(key)
	
	#if cv2.waitKey(2) & 0xFF == ord('q'): # milliseconds
	#	break

	if play:
		currentFrame += 1
		if currentFrame>nFrames-1:
			currentFrame = nFrames-2
		cap.set(cv2.CAP_PROP_POS_FRAMES, currentFrame)
		ret, frame = cap.read()
		adjustBrightness()
		milliseconds = round(cap.get(cv2.CAP_PROP_POS_MSEC),2)
		
cap.release()
cv2.destroyAllWindows()
