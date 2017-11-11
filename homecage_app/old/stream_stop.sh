#!/bin/bash

	uv4lPID=`pgrep -f uv4l`
	if [ -n "$uv4lPID" ]; then
		echo "stopping video stream"
		#sudo pkill uv4l
		pkill uv4l
	else
		echo "video stream is not running, use 'stream start' to start."
		exit 1
	fi
