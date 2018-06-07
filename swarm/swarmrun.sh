#!/bin/bash

# general purpose script to run scripts/commands on a number of remote machines
#
#usage:
#	./swarmrun.sh ip.list

# 1
# assumes an rsa public/private key has been generated on *this machine
# will ask you for the follownig for each machine
# 1) yes to accept initial authentification
# 2) password to login

#todo: at home I made the commander have swarm.git server, 
#      at work I need an extra pi to hold homecage.git
#      this machine can do double-time as the main video wall server

# 192.168.1.3 is my swarm commander
commanderIP="192.168.1.3"

while IFS='' read -r line || [[ -n "$line" ]]; do
	
	echo '=== '$line' ==='
	
	# copy rsa key from *this machine to each remote
	# once this is done, *this machine can login to all remotes without a password
	#ssh-copy-id pi@$line
	
	# on each remote, generate rsa key and copy back to *this
	# this is too complicated, do it by hand
	# if a remote machine key get rewritten, we will have trouble logging in
	#genRsaCmd="rm ~/.ssh/id_rsa; ssh-keygen -f /home/pi/.ssh/id_rsa -N ''; ssh-copy-id pi@$commanderIP"
	#echo $genRsaCmd
	#ssh pi@$line "$genRsaCmd"
	
	#on each remote machine, make initial clone
	#gitCloneCommand="git clone ssh://pi@$commanderIP/~/homecage.git/homecage;"
	#ssh pi@$line "$gitCloneCommand" 

	# on each remote, run homecage install script
	#installCmd="cd homecage/homecage_app; ./install-homecage.sh;"
	#installCmd="cd homecage/homecage_app; ./install.sh;"
	#ssh pi@$line "$installCmd" 
	
	# on each remote, update homecage
	#updateCmd="sudo systemctl stop homecage.service; cd homecage; git pull; sudo systemctl start homecage.service;"
	#ssh pi@$line "$updateCmd" 
	
	# start/stop/restart homecage server on each remote
	#restartCmd="sudo systemctl start homecage.service;"
	restartCmd="sudo systemctl stop homecage.service;"
	#restartCmd="sudo systemctl restart homecage.service;"
	ssh pi@$line "$restartCmd" 

done < "$1"

