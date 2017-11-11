#!/bin/bash

echo "$#"

if [ "$#" -ne 2 ]; then
	streamWidth=640
	streamHeight=480
else
	streamWidth=$1
	streamHeight=$2
fi

	videoPID=`pgrep -f video.py`
	if [ -n "$videoPID" ]; then
		echo "video is recording, use 'record stop' to stop."
		exit 1
	fi

	uv4lPID=`pgrep -f uv4l`
	if [ -n "$uv4lPID" ]; then
		echo "stream is already running, use 'stream stop' to stop."
		echo "trying to kill stream"
		stream_stop.sh
		#exit 1
	fi

	#h264
	uv4l --verbosity=-1 --driver raspicam --auto-video_nr --encoding h264 --width $streamWidth --height $streamHeight --enable-server on
	#uv4l --verbosity=-1 --driver raspicam --auto-video_nr --encoding h264 --width $1 --height $2 --enable-server on
	#uv4l --verbosity=-1 --driver raspicam --auto-video_nr --encoding h264 --width 640 --height 480 --enable-server on
	#uv4l --verbosity=-1 --driver raspicam --auto-video_nr --encoding h264 --width 1280 --height 720 --enable-server on
	
	ip=`ifconfig eth0 | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1'`
	
	echo $streamWidth $streamHeight
	echo View the stream at:
	echo "   "http://$ip:8080/stream
