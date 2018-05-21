Homecage is a Raspberry Pi camera controller.

## Features

- Record
- Stream
- Record on GPIO trigger

## Install

Clone repository

	https://github.com/cudmore/homecage.git
	
### Either install python packages globally

	pip install -r requirements.txt

### Or install in virtual env

Make a clean virtual environment that does not depend on current installed packages

	# make a python 2 environment for now
	#virtualenv -p python2 --no-site-packages env
	
	# make a python 3 environment
	virtualenv -p python3 --no-site-packages env

Activate the environment

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


