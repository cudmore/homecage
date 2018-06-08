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
echo '=== 4/5: Installing videowall Python requirements with pip'
echo '==='
pip install -r requirements.txt

deactivate

# copy 
echo ' '
echo '==='
echo '=== 5/5: Configuring systemctl in /etc/systemd/system/videowall.service'
echo '==='
sudo cp bin/videowall.service /etc/systemd/system/videowall.service
sudo chmod 664 /etc/systemd/system/videowall.service
sudo systemctl daemon-reload
sudo systemctl enable videowall.service
sudo systemctl start videowall.service
#sudo systemctl status homecage.service

echo ' '
echo 'Done installing videowall server. The videowall server is running and will run at boot.'
echo 'To use the server, point your browser to:'
echo "    http://$ip:8000"
