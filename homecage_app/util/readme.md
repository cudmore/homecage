System utilities to set up the Pi. We need these when we have a swarm/cluster of Pi.

## install-usb.sh

Bash script to detect and permanently mount an external USB drive. Assumes drive is at /dev/sda1 and the mount point is /home/pi/video

## sethostname.sh

Bash script to set (i) hostname and (ii) afp mount point

sudo hostnamectl set-hostname hc0

