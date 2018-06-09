#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180607
# Purpose: Bash script to install and run videowall_app
#	1) create a python3 virtual environment
#	2) install videowall_app/requirements.txt
#	3) install a systemctl service videowall.service
#
# Usage:
#	./install-videowall.sh
#
# Once this is all done, videowall server can be used as follows
# sudo systemctl start videowall.service
# sudo systemctl stop videowall.service
# sudo systemctl restart videowall.service
# sudo systemctl enable videowall.service
# sudo systemctl disable videowall.service

if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

ip=`hostname -I | xargs`

sudo systemctl stop videowall.service

if ! type "pip" > /dev/null; then
	echo '==='
	echo "=== Installing pip"
	echo '==='
	sudo apt-get -y install python-pip
fi

if ! type "virtualenv" > /dev/null; then
	echo '==='
	echo "=== Installing virtualenv"
	echo '==='
	sudo /usr/bin/easy_install virtualenv
fi

echo '==='
echo "=== Making Python 3 virtual environment in $PWD/env"
echo '==='
if [ ! -d "env/" ]; then
	mkdir env
	virtualenv -p python3 --no-site-packages env
fi

source env/bin/activate

echo ' '
echo '==='
echo '=== Installing videowall Python requirements with pip'
echo '==='
pip install -r requirements.txt

deactivate

# copy 
echo ' '
echo '==='
echo '=== Configuring systemctl in /etc/systemd/system/videowall.service'
echo '==='
sudo cp bin/videowall.service /etc/systemd/system/videowall.service
sudo chmod 664 /etc/systemd/system/videowall.service
sudo systemctl daemon-reload
sudo systemctl start videowall.service
sudo systemctl enable videowall.service

echo ' '
echo 'Done installing videowall server. The videowall server is running and will run at boot.'
echo 'To use the server, point your browser to:'
echo "    http://$ip:8000"
