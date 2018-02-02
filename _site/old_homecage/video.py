import os
import datetime
import picamera

actuallyRecord = 1
videoDuration = 60*5 #seconds

#the start time stamp of the script (determines directory)
now = datetime.datetime.now()
dateStr = now.strftime('%Y%m%d')

#make destination direcory
dstDir = '/home/pi/video/' + dateStr + '/'
if not os.path.exists(dstDir):
    os.makedirs(dstDir)

abortedDuringAcquisition = False

while True:
    try:
        with picamera.PiCamera() as camera:
            #camera.stop_recording()

            if(actuallyRecord==1):
                #camera.resolution = (2592, 1944)
                camera.resolution = (640, 480)
		camera.framerate = 15
        
                startTime = datetime.datetime.now()
                startTimeStr = startTime.strftime('%Y%m%d_%H%M%S')
        
                #the file we are about to record/save
                thisVideoFile = dstDir + startTimeStr + '.h264'

                print('Start: dur=' + str(videoDuration) + ' file=' + thisVideoFile)

                try:
                    #camera.start_recording(thisVideoFile, resize=(1024, 768))
                    camera.start_recording(thisVideoFile, resize=(640, 480))
                    camera.wait_recording(videoDuration)
                    camera.stop_recording()
                except KeyboardInterrupt:
                    print ' -->> aquisition cancelled'
                    abortedDuringAcquisition = True
                    raise

                stop = datetime.datetime.now()
                stopStr = stop.strftime('%Y%m%d_%H%M%S')

                print('  Stop:  ' + stopStr)
    
                #todo: log what we just did
                #todo: check temparature and humidity and lof to file
                #todo: check time and turn IR/White lights on and or off

    except KeyboardInterrupt:
        #print 'Terminated with a user pressing ctrl-c'
        #print '    last file was: ' + thisVideoFile
        if abortedDuringAcquisition and os.path.isfile(thisVideoFile):
            print ' Removing last file:' + thisVideoFile
            #there is a chance we get here and the file was done
            #todo: user should be responsible for removing last file?
            os.remove(thisVideoFile)
        break

