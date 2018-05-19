#!/bin/bash

# avconv -i 20171201_091431.h264 -r 30 -vcodec copy mp4/20171201_091431.mp4

#todo: we are now saving in same directory
# simplify this by (1) remove .h264, dst will then just have .mp4

# get file name without extension
filename=$(basename "$1")
filename="${filename%.*}"

# get the source directory from full path to file
mydir=$(dirname $1)

# make full path to output file
# this is really bad form, hard to read (my fault)
#dstfile=$mydir'/mp4/'$filename'.mp4'
dstfile=$mydir'/'$filename'.mp4'

#cmd="avconv -i $1 -r $2 -vcodec copy $dstfile"
cmd="avconv -loglevel error -framerate $2 -i $1 -vcodec copy $dstfile"
echo $cmd
$cmd