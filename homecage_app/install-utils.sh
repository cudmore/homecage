#!/bin/bash

# Author: Robert H Cudmore
# Date: 20180603
# Purpose: Bash script to
#	1) install uv4l for video streaming
#	2) install avconv to convert .h264 video files to .mp4

#
# install uv4l
printf '\n=== 1/5 downloading apt-key with curl\n'

curl http://www.linux-projects.org/listing/uv4l_repo/lpkey.asc | sudo apt-key add -

# check if stretch_install is already n file /etc/apt/sources.list
printf '\n=== 2/5 checking you are running either jessie or stretch\n'
if cat /etc/os-release | grep -q "stretch"
then
	echo '   you are running stretch'
	uv4l_deb='deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/stretch stretch main'
fi

if cat /etc/os-release | grep -q "jessie"
then
	echo '   you are running jessie'
	uv4l_deb='deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/ jessie  main'
fi

# if uv4l_deb is empty, neither stretch or jessie -->> ERROR
if [[ -z  $uv4l_deb  ]] && echo "error: uv4l will only install on jessie or stretch"
then
	exit 1
fi

printf '\n=== 3/5 checking /etc/apt/sources.list\n'
if grep -xq "$uv4l_deb" /etc/apt/sources.list
then
	# found
	echo 'warning: /etc/apt/sources.list already has the line'
	echo '   ' $uv4l_deb
else
	# not found
	echo 'appending line to /etc/apt/sources.list'
	echo '   ' $uv4l_deb
	echo $uv4l_deb | sudo tee -a /etc/apt/sources.list
fi

printf '\n=== 4/5 installing uv4l (please wait)\n'
sudo apt-get -qq update
sudo apt-get -qq install uv4l uv4l-server uv4l-raspicam

#
# install avconv
printf '\n=== 5/5 installing libav-tools (e.g. avconv)\n'
sudo apt-get -qq install libav-tools

exit 0