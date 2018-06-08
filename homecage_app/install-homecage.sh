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
# sudo systemctl start homecage.service
# sudo systemctl stop homecage.service
# sudo systemctl restart homecage.service
# sudo systemctl enable homecage.service
# sudo systemctl disable homecage.service

if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

ip=`hostname -I | xargs`

echo '==='
echo "=== 1/5: Installing pip"
echo '==='
sudo apt-get install python-pip

echo '==='
echo "=== 2/5: Installing virtualenv"
echo '==='
sudo /usr/bin/easy_install virtualenv

echo '==='
echo "=== 3/5: Making Python 3 virtual environment in $PWD/env"
echo '==='
if [ ! -d "env/" ]; then
	mkdir env
fi

virtualenv -p python3 --no-site-packages env
source env/bin/activate

echo ' '
echo '==='
echo '=== 4/5: Installing homecage Python requirements with pip'
echo '==='
pip install -r requirements.txt

deactivate

# copy 
echo ' '
echo '==='
echo '=== 5/5: Configuring systemctl in /etc/systemd/system/homecage.service'
echo '==='
sudo cp bin/homecage.service /etc/systemd/system/homecage.service
sudo chmod 664 /etc/systemd/system/homecage.service
sudo systemctl daemon-reload
sudo systemctl enable homecage.service
sudo systemctl start homecage.service
#sudo systemctl status homecage.service

echo ' '
echo 'Done installing homecage server. The homecage server is running and will run at boot.'
echo 'Remember to install uv4l and avconv with ./install-extras.sh'
echo 'To use the server, point your browser to:'
echo "    http://$ip:5000"
