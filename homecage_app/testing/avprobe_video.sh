#!/bin/bash

# check that avprobe is available
type avprobe >/dev/null 2>&1 || { echo >&2 "avprobe not installed"; exit 1; }

cmd="avprobe -show_format -show_streams -loglevel quiet $1 -of json"
#echo $cmd
$cmd

exit 0