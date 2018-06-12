# 20180609
# Robert Cudmore

# we want to add something like this to /etc/fstab
# UUID=413A-14EA /home/pi/video    vfat    rw,umask=0      0       0

if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

myfolder="/home/pi/video"
this_sda="/dev/sda1"

# make the mount point folder if it does not exist
if [ ! -d "$myfolder" ]; then
	# not found
	echo "making directory with mkdir $myfolder"
	mkdir $myfolder
fi

# get the uuid from mounted usb at /dev/sda1
echo "searching for a UUID at $this_sda"

if [ ! -b "$this_sda" ]; then
	# not found
	echo "warning: did not find a block file at $this_sda"
	echo "exiting with no action taken"
	exit 1
fi

uuid=$(lsblk -no UUID $this_sda)
echo "ok: found $this_sda with UUID=$uuid"

if [[ -z "$uuid" ]];
then
	echo "warning: no UUID found for $this_sda"
	echo "exiting with no action taken"
	exit 1
fi

# check if this uuid is in /etc/fstab
echo "checking if UUID=$uuid is already in /etc/fstab"
if grep -q "UUID=$uuid" /etc/fstab;
then
    # found
    echo "ok: /etc/fstab already has the entry: "$(grep  "$uuid" /etc/fstab)
    echo "exiting with no action taken"
    exit 0
else
    # not found
    mynewline="UUID=$uuid $myfolder    vfat    rw,umask=0      0       0"
    echo "ok: appending entry to fstab: "$mynewline
    echo $mynewline | sudo tee -a /etc/fstab
    sudo mount -a
fi

echo "done: your usb drive should be available in $myfolder"

exit 0