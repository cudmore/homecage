# 20180609
# Robert Cudmore

# bash script to set
#	1) hostname
#	2) afp mount point
#
# Usage:
#	./sethostname "newhostname"

#
# 1) set the hostname
#

if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

# make sure we get $1
if [[ -z "$1" ]]
then
	echo 'Error: Usage is: ./sethostname.sh "my_host_name"'
	exit 1
fi

sudo hostnamectl set-hostname "$1"

#
# 2) set afp mount point
#

sudo /etc/init.d/netatalk stop;

#myhostname="swarmcommander"
# search in /etc/netatalk/AppleVolumes.default
# for the line '~/ "'
# and replace it with '~/ "hc1"'
#sudo sed -i "s/.*~\/.*/~\/ \"$myhostname\"/" /etc/netatalk/AppleVolumes.default
sudo sed -i "s/.*~\/.*/~\/ \"$1\"/" /etc/netatalk/AppleVolumes.default

#
# THIS IS REALLY BAD. EACH TIME SCRIPT IS RUN WE ARE APPENDING
#

# to make a video mountpoint
videomount="/home/pi/video \"$1_video\""
echo $videomount
echo $videomount | sudo tee -a /etc/netatalk/AppleVolumes.default

sudo /etc/init.d/netatalk start

echo "Done"

exit 0