# Treadmill

A web server to control an on-the-scope experiment with video and a motorized treadmill.

Features:
 - Flexible video recording
 - Video streaming in your browser
 - Start and stop video recording with hardware triggers
 - Watermark video with precise frame numbers
 - Control a motor during video recording (requires Teensy microcontroller)
 - Saves all events during experiments into an easy to parse text file

## Install treadmill server

Install treadmill server

	cd homecage/treadmill
	./install-treadmill.sh

Thats it. The treamill server is running and will run at boot. You can use the web interface at http://[ip]:5010

## Install extras for video streaming and conversion

	cd homecage/treadmill
	./install-extras.sh

## Using a Teensy

This requires a few simple system wide configurations. See the readme in homecage/treadmill/platformio
	
## Troubleshooting

	cd ~/homecage/treadmill
	
	# stop the treadmill service
	./treadmill stop
	
	# run server manually
	source env/bin/activate
	python treadmill_app.py debug
	