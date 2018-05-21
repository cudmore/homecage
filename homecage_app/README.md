Homecage is a Raspberry Pi camera controller.

## Features

- Record
- Stream
- Record on GPIO trigger

## Check your system

homecage runs best on raspberry 2/3 and Debian stretch. Do not run it on Raspberry Model B, it is too slow.

Check which version of the Raspberry Pi you have (you should have a Raspberry 2/3)

	cat /proc/device-tree/model

Check your Debian version (you should be using Debian Stretch)

	cat /etc/os-release


## Install uv4l for streaming

	curl http://www.linux-projects.org/listing/uv4l_repo/lrkey.asc | sudo apt-key add -

	# edit /etc/apt/sources.list
	sudo pico /etc/apt/sources.list
	
	# add the following line to /etc/apt/sources.list
	deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/stretch stretch main

	sudo apt-get update
	sudo apt-get install uv4l uv4l-raspicam

## Install avconv to convert video format from .h264 to .mp4

	#sudo apt-get update
	sudo apt-get install libav-tools

## Install homecage

Clone repository

	# install git if necessary
	sudo apt-get install git
	
	# clone homecage
	git clone --depth=1 https://github.com/cudmore/homecage.git

### Either install python packages globally

	cd homecage/homecage_app
	pip install -r requirements.txt

### Or install in virtual environment

Make a clean virtual environment that does not depend on current installed Python packages

	# install virtualenv if necessary
	pip install virtualenv
	
	cd homecage/homecage_app
	
	mkdir env
	
	
	# make a python 2 environment for now
	#virtualenv -p python2 --no-site-packages env
	
	# make a python 3 environment
	virtualenv -p python3 --no-site-packages env

Activate the environment. Once activated, the command prompt will begin with '(env)'

	source env/bin/activate

Check your python version

	python -V
	
Make sure python command is running in the virtual environment

	which python

Install homecage_app dependencies

	pip install -r requirements.txt 

Run homecage_app.py

	python homecage_app.py

Browse to the homecage_App website

	http://[yourip]:5000
	
Exit virtual environment

	deactivate
	

## Running

Run the server

	python homecage_app.py

Browse to server homepage

	http://[yourip]:5000
			
## REST API

/simulate/triggerin

/simulate/frame

/simulate/stop

## Troubleshooting

pip 10 seems to be broken. Uninstall and then install pip 9

	# uninstall pip
	python -m pip uninstall pip
	
	# install pip 9
	python -m pip install -U "pip<10"
	
if virtualenv is not available (16.0.0)

	sudo /usr/bin/easy_install virtualenv


