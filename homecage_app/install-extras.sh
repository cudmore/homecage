#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180603
# Purpose: Bash script to
#	1) install uv4l for video streaming
#	2) install avconv to convert .h264 video files to .mp4

if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

echo '==='
echo '=== 1/3 Configuring source repositories for uv4l'
echo '==='

curl http://www.linux-projects.org/listing/uv4l_repo/lrkey.asc | sudo apt-key add -

# check if stretch_install is already n file /etc/apt/sources.list
if cat /etc/os-release | grep -q "stretch"
then
	echo 'Good, you are running Raspian Stretch'
	uv4l_deb='deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/stretch stretch main'
fi

if cat /etc/os-release | grep -q "jessie"
then
	echo 'Good, you are running Raspian Jessie'
	uv4l_deb='deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/ jessie  main'
fi

# if uv4l_deb is empty, neither stretch or jessie -->> ERROR
if [[ -z  $uv4l_deb  ]] && echo "ERROR: uv4l will only install on raspian jessie or stretch"
then
	#exit 1
	echo ''
else

	#echo '=== 3/5 checking /etc/apt/sources.list'
	if grep -xq "$uv4l_deb" /etc/apt/sources.list
	then
		# found
		#echo 'OK: /etc/apt/sources.list already has the line'
		#echo '   ' $uv4l_deb
		echo ''
	else
		# not found
		echo 'Appending line to /etc/apt/sources.list'
		#echo '   ' $uv4l_deb
		echo $uv4l_deb | sudo tee -a /etc/apt/sources.list
	fi

	echo '==='
	echo '=== 2/3 Installing uv4l (please wait)'
	echo '==='
	sudo apt-get -qq update
	sudo apt-get -qq --allow-unauthenticated install uv4l uv4l-server uv4l-raspicam

fi

echo ' '
echo '==='
echo '=== 3/3 installing libav-tools (e.g. avconv)'
echo '==='
sudo apt-get -qq install libav-tools

echo ' '
if [[ -z  $uv4l_deb  ]];
then
	echo 'WARNING: uv4l did NOT install, you need to be running raspian jessie or stretch. Streaming will not work'
else
	echo 'Done installing uv4l'
fi
echo 'Done installing libav-tools (e.g. avconv)'

exit 0