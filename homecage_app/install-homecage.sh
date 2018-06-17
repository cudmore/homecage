#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180603
# Purpose: Bash script to install homecage
#	1) create a python3 virtual environment
#	2) install homecage_app/requirements.txt
#	3) install a systemctl service homecage.service
#
# Usage:
#	./install-homecage.sh
#
# Once this is all done, homecage server can be used as follows
#	cd homecage/homecage_app
#	./homecage start
#	./homecage stop
#	./homecage restart
#	./homecage status
#	./homecage enable		# start homecage server at boot
#	./homecage disable		# do not start homecage server at boot

if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

ip=`hostname -I | xargs`

#if systemctl is-active --quiet homecage.service; then
#	echo 'service is active'
#fi

sudo systemctl stop homecage.service

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
echo '=== Installing homecage Python requirements with pip'
echo '==='
pip install -r requirements.txt

deactivate

# copy 
echo ' '
echo '==='
echo '=== Configuring systemctl in /etc/systemd/system/homecage.service'
echo '==='
sudo cp bin/homecage.service /etc/systemd/system/homecage.service
sudo chmod 664 /etc/systemd/system/homecage.service
sudo systemctl daemon-reload
sudo systemctl start homecage.service
sudo systemctl enable homecage.service
#sudo systemctl status homecage.service

echo ' '
echo 'Done installing homecage server. The homecage server is running and will run at boot.'
echo 'Remember to install uv4l and avconv with ./install-extras.sh'
echo 'To use the server, point your browser to:'
echo "    http://$ip:5000"
