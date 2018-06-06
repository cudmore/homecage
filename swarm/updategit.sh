#1 shut down homecage
systemctl stop homecage.service

#2 synch with git (make sure password works!)
cd homecage/homecage_app
git checkout master
git pull

#3 restart homecage
systemctl start homecage.service
