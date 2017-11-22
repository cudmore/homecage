
## 1) Log in to the Pi

On a Mac, use the terminal application in /Applications/Utilities/terminal.app
 
	# Type
	ssh pi@10.16.80.162

	# Enter password
	poetry7

## 2) Change into the homecage directory

At the command prompt, type

	cd /Sites/homecage

## 3) Get command help

The commands allow you to start and stop a video stream and video recording. They can also be used to turn the white and IR lights on and off.

To get help, at the command prompty, type 

	./help

This returns

	 Status
		status - check the status
	 Video Recording
		record start
		record stop
	 Video Streaming
		stream start
		stream stop
	 IR Light
		light ir on
		light ir off
	 White Light
		light white on
		light white off

## 4) Position the cages within a good field-of-view

Start a video stream and then view the stream in a web browser.

	stream start

	# Returns
	View the stream at:
   	   http://10.16.80.162:8080/stream

In any browser, go to the address `http://10.16.80.162:8080/stream`

While positioning cages, turn the white and or IR LEDs on and off

	# Turn the white lights on
	light white on
	
	# Turn the white lights off
	light white off

When your happy with position, stop the video stream

	stream stop

## 5) Start continuous video recording

	record start
	
This will save recorded video into individual files, 5 minutes of video per file. This will also control the light cycle, at night (6 PM - 6 AM) the white light is off and the IR light is on. During the day (6 AM - 6 PM), the white light is on and the IR light is off. Both the duration of each video file at the timing of the light cycle can easily be changed.

## 6) Mount the file server to get your video files

On a Mac, use `Finder -> Go -> Connect To Server...` and log in as follows

	afp://10.16.80.162
	username: pi
	password: poetry7d

Files are saved in the `/video/` folder. Video files have the .h264 extension. There are also text files (extension .txt) saved, these have a log of temperature and humidity as well as the time the lights were turned on and off.

## 7) Log out of the Pi

	exit