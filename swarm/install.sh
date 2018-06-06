# 20180606
# Robert Cudmore

# script to download and install homecage on a remote machine
# install should enable systemctl homecage.service
# after this is done, should be able to browse
#    http:[IP]:5000

#usage:
#  ssh pi@192.168.1.31 'bash -s' < ./install.sh 

git clone --depth=1 https://github.com/cudmore/homecage.git
cd homecage/homecage_app
./install.sh
