#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180603
# Purpose: Bash script to install treadmill
#	1) create a python3 virtual environment
#	2) install treadmill/requirements.txt
#	3) install a systemctl service treadmill.service
#
# Usage:
#	./install-treadmill.sh
#
# Once this is all done, treadmill server can be used as follows
#	cd homecage/treadmill
#	./treadmill start
#	./treadmill stop
#	./treadmill restart
#	./treadmill status
#	./treadmill enable		# start homecage server at boot
#	./treadmill disable		# do not start homecage server at boot

if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

ip=`hostname -I | xargs`

#if systemctl is-active --quiet treadmill.service; then
#	echo 'service is active'
#fi

sudo systemctl stop treadmill.service

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

if [ ! -d "env/" ]; then
	echo '==='
	echo "=== Making Python 3 virtual environment in $PWD/env"
	echo '==='
	mkdir env
	virtualenv -p python3 --no-site-packages env
fi

source env/bin/activate

echo ' '
echo '==='
echo '=== Installing treadmill Python requirements with pip'
echo '==='
pip install -r requirements.txt

deactivate

# copy 
echo ' '
echo '==='
echo '=== Configuring systemctl in /etc/systemd/system/treadmill.service'
echo '==='
sudo cp bin/treadmill.service /etc/systemd/system/treadmill.service
sudo chmod 664 /etc/systemd/system/treadmill.service
sudo systemctl daemon-reload
sudo systemctl start treadmill.service
sudo systemctl enable treadmill.service
#sudo systemctl status treadmill.service

echo ' '
echo 'Done installing treadmill server. The treadmill server is running and will run at boot.'
echo 'To use the server, point your browser to:'
echo "    http://$ip:5010"
