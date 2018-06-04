#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180603
# Purpose: Bash script to
#	1) create a python3 virtual environment
#	2) install homecage_app/requirements.txt
#	3) add homecage_app/bin to path
#
# Usage:
#	source install-homecage.sh
#
# Once this is all done, homecage server can be used as follows
# homecage start
# homecage start debug
# homecage stop
# homecage restart
# homecage status


printf '\n === 1/5: mkdir env \n'
mkdir env

printf '\n === 2/5: virtualenv -p python3 --no-site-packages env \n'
virtualenv -p python3 --no-site-packages env

printf '\n === 3/5: source env/bin/activate \n'
source env/bin/activate

printf '\n === 4/5: pip install -r requirements.txt \n'
pip install -r requirements.txt

deactivate

#
# append to .bashrc if neccessary
bash_append='export PATH='"$PWD/bin"':$PATH'

printf '\n === 5/5 Updating $PATH \n'

if [[ ":$PATH:" == *":$PWD/bin:"* ]]; then
  echo "   OK: Your path already contains $PWD/bin"
else
  echo '   Your $PATH is missing '"$PWD"'/bin, appending to '"$HOME"'/.bashrc'
	echo '      '$bash_append
	echo $bash_append | tee -a $HOME/.bashrc
fi

#
# make a homecage_dir variable so bin/homecage knows where it is installed
printf "\n === 6/6: Checking that homecage_path=$PWD \n"
if [[ "$homecage_path" == "$PWD" ]]; then
  echo "   OK: Your homecage_path is already set to $PWD"
else
	echo "   Appending to $HOME/.bashrc"
	tmp='export homecage_path="'"$PWD"'"'
	echo '      '$tmp
	echo $tmp | tee -a $HOME/.bashrc
fi

source $HOME/.bashrc

# copy 
printf '\n 7/7: Configuring systemctl homecage.service \n'
sudo cp homecage.service /etc/systemd/system/homecage.service
sudo chmod 664 /etc/systemd/system/homecage.service
sudo systemctl daemon-reload
sudo systemctl enable homecage.service
sudo systemctl start homecage.service
sudo systemctl status homecage.service

printf 'Done installing homecage server.'
