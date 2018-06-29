# Treadmill

A web server to control an on-the-scope experiment with video and a motorized treadmill.

System Requirements:
 - Raspberry Pi 2/3
 - Raspberry Pi Camera
 
Features:
 - Video recording
 - Video streaming to a browser
 - Start and stop video recording with hardware triggers
 - Watermark video with incoming events including frame numbers
 - Control a motor during video recording (requires Teensy microcontroller)
 - Saves all events into an easy to parse text file

## Download

	# if you don't already have git
	# sudo apt-get install git
	
	git clone xxx
	
## Install treadmill

	cd ~/homecage/treadmill
	./install-treadmill.sh

Thats it. You can run the treadmill server with `./treadmill start` and use the web interface at http://[ip]:5010

## Install extras

Install uv4l for video streaming and avconv for video conversion

	cd ~/homecage/treadmill
	./install-extras.sh

Install a DHT temperature/humidity sensor

	cd ~/homecage/treadmill
	./install-dht.sh
	
## Running the treadmill server

The `./treadmill-install.sh` command installs a system service allowing the treadmill server to be controlled. For example:

	cd ~/homecage/treadmill
	./treadmill start
	./treadmill stop
	./treadmill restart
	./treadmill status
	./treadmill enable    - enable treadmill at boot
	./treadmill disable   - disable treadmill at boot

	./treadmill run     - run treadmill on command line
	./treadmill debug     - run treadmill on command line (debug mode)
	
## Using a Teensy

This requires a few simple system wide configurations. See the readme in `homecage/treadmill/platformio`.
	
## Troubleshooting

	# make sure the treadmill service is stopped
	cd ~/homecage/treadmill
	./treadmill stop
	
	# run the treadmill server and output logs to the command prompt
	./treadmill run
	
## Activating serial ports

Run the raspberry pi configuration utility

	sudo raspi-config

And select the following

	5 Interfacing Options - Configure connections to peripherals 

	P6 Serial - Enable/Disable shell and kernel messages on the serial connection  
	
	Would you like a login shell to be accessible over serial? -->> No

	Would you like the serial port hardware to be enabled?   -->> Yes
