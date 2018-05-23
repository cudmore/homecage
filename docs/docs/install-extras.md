
## Start homecage_app at boot (optional)

Edit crontab

    crontab -e
    
Add the following line to the end of the file (make sure it is one line)

```
@reboot (sleep 10; cd /home/pi/homecage/homecage_app && /usr/bin/python /home/pi/homecage/homecage_app/homecage_app.py)
```

If you do this it is important to be able to find the running homecage_app, in case you want to force it to quit.

```
# at a command prompt, type this
ps -aux | grep homecage_app

# and you will get something like this
pi       12445  9.5  2.2  41572 20200 pts/2    Sl   17:14   0:01 python homecage_app.py
pi       12468 13.4  2.3  51032 20508 pts/2    Sl   17:14   0:01 /usr/bin/python homecage_app.py

# kill both processes running homecage_app
kill -9 12455
kill -9 12468
```

##File Server

It is easy to make the Raspberry Pi a file server. Once either Apple-File-protocol (afp) or Samba (smb) are installed you can mount the Raspberry Pi like any other file server.

### MacOS

The Pi can be manually mounted from MacOS by going to `Go - Connect To Server...` and entering `afp://IP` where IP is the IP address of your Pi.
	    
### Windows

To mount the Pi in Windows, click on the Start menu and type `smb:\\IP` where IP is the IP address of your Pi.

## Install Apple-file-protocol (afp, also known as Netatalk)

This will make the Pi an apple-file-protocol file-server that can be accessed in MacOS.

    sudo apt-get install netatalk

Once netatalk is installed, the Raspberry will show up in the Mac Finder 'Shared' section. 

### Change the default name of your Pi in netatalk

When you mount the pi on MacOS, it will mount as 'Home Directory' and the space in 'Home Directory' will cause problems. Change the name to something like 'pi3'.

See [this blog post][afpmountpoint] to change the name of the mount point from 'Home Directory'.    

In the following `the_name_you_want` should be changed to the name you want.

    # stop netatalk
    sudo /etc/init.d/netatalk stop

    # edit config file
    sudo pico /etc/netatalk/AppleVolumes.default

    # change this one line

    # By default all users have access to their home directories.
    #~/                     "Home Directory"
    ~/                      "the_name_you_want"

    # restart netatalk
    sudo /etc/init.d/netatalk start

When in pico, you can search for a string with control+w and you can exit with control+x.

## Install Samba (smb)

This will make the Pi a Samba (SMB) file server that can be accessed from both Windows and MacOS.

    sudo apt-get install samba samba-common-bin

Edit `/etc/samba/smb.conf`

	sudo pico /etc/samba/smb.conf

Add the following

	[share]
	Comment = Pi shared folder
	Path = /home/pi
	Browseable = yes
	Writeable = Yes
	only guest = no
	create mask = 0777
	directory mask = 0777
	Public = yes
	Guest ok = no

Add a password

	sudo smbpasswd -a pi

Restart samba

	sudo /etc/init.d/samba restart
	
Test the server from another machine on the network. On a windows machine, mount the fileserver with `smb:\\IP` where IP is the IP address of your pi.
   

## Install DHT temperature sensor (optional)

You can acquire reasonably accurate temperature and humidity readings with an inexpensive temperature sensort like the [DHT-Temperature Sensor][dht]. If you run into trouble then go to [this tutorial][7]. If you don't do this, homecage should work but you won't be able to read the temperature and humidity.
    
    cd
    mkdir tmp
    cd tmp
    git clone https://github.com/adafruit/Adafruit_Python_DHT.git
    cd Adafruit_Python_DHT
    sudo python setup.py install

## Startup tweet

Have the Pi send a tweet with its IP when it boots. See [this blog post][startuptweeter] for instructions.
	
## Startup mailer

Have the Pi send an email with its IP address when it boots. See [this blog post][startupmailer] for instructions. An example python script is here, [startup_mailer.py][startupmailer.py]


[1]: http://blog.cudmore.io/post/2017/11/22/raspian-stretch/
[7]: https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/software-install-updated
[dht]: https://www.adafruit.com/product/385?gclid=CjwKCAiA9f7QBRBpEiwApLGUip6TE2XPQx_9hVrRY83GHtGapdZq6H4t1ZHUJfuRXRTZdBMLvbmCJhoCWC4QAvD_BwE
[afpmountpoint]: http://blog.cudmore.io/post/2015/06/07/Changing-default-mount-in-Apple-File-Sharing/
[startupmailer.py]: https://github.com/cudmore/cudmore.github.io/blob/master/_site/downloads/startup_mailer.py
[startupmailer]: http://blog.cudmore.io/post/2017/11/28/startup-mailer/
[startuptweeter]: http://blog.cudmore.io/post/2017/10/27/Raspberry-startup-tweet/