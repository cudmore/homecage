# 20180609
# Robert Cudmore
#
# bash script to set
#	1) hostname
#	2) afp mount point
#
# Usage:
#	./sethostname "newhostname"
#
#
# This assumes /etc/netatalk/AppleVolumes.default
# already has 2x lines I appended by hand
#
#		~/ "hc1" #homecage_home
#		/home/pi/video "hc1_video" #homecage_video
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

echo "setting hostname to '$1'. Reboot required"
sudo hostnamectl set-hostname "$1"

#
# 2) set afp mount point
#

#sudo /etc/init.d/netatalk stop;

#myhostname="swarmcommander"
# search in /etc/netatalk/AppleVolumes.default
# for the line '~/ "'
# and replace it with '~/ "hc1"'
#sudo sed -i "s/.*~\/.*/~\/ \"$myhostname\"/" /etc/netatalk/AppleVolumes.default
# replace line containing '~/'
sudo sed -i "s/.*~\/.*/~\/ \"$1\"/" /etc/netatalk/AppleVolumes.default

# make a video mountpoint (escaping / with \ for sed)
videofolder='\/home\/pi\/video'
videomount="/home/pi/video \"$1_video\""
echo "video mount point: $videomount"
# remove line containing $
sudo sed -i "s/.*$videofolder.*//" /etc/netatalk/AppleVolumes.default

# append
echo $videomount | sudo tee -a /etc/netatalk/AppleVolumes.default

sudo /etc/init.d/netatalk start

echo "Done: Hostname and afp are now: $1 --- REBOOT REQUIRED"

exit 0
