# synch 2 machines with ssh-key

## 1) create a key on a local machine

    ssh-keygen

This makes a private and a public key

    ~/.ssh/id_rsa 
    ~/.ssh/id_rsa.pub 

## 2) Transfer key to a remote machine

	ssh-copy-id pi@192.168.1.31

Will need to enter password this last time

## 3) login to remote machine and don't need a password


# run a bash script on remote machine

    ssh pi@192.168.1.31 'bash -s' < ./script.sh 


## install script

```
git clone --depth=1 https://github.com/cudmore/homecage.git
cd homecage/homecage_app
./install.sh
```

## Git script

```
#1 shut down homecage
systemctl stop homecage.service

#2 synch with git (make sure password works!)
cd homecage/homecage_app
git checkout master
git pull

#3 restart homecage
systemctl start homecage.service
```

## To Do

- modify startup mailer to include MAC address