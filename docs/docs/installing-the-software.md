# Install homecage

We will assume you have a functioning Raspberry Pi. To get started setting up a Pi from scratch, see our [setup intructions][0]. We will also assume you are logged in to the Pi using terminal on OSX or [Putty][putty] on Windows.

## 1) Check your system

Homecage runs best on a Raspberry 2/3 and Debian stretch. **Do not run it on Raspberry Model B, it is too slow**.

Check which version of the Raspberry Pi you have.

```
#at a command prompt, type
cat /proc/device-tree/model

#you should get something like this
Raspberry Pi 3 Model B Rev 1.2
```

Check which version of the Debian operating system you have. You should have a Debian Stretch

```
#at a command prompt, type
cat /etc/os-release

#you should get something like this
PRETTY_NAME="Raspbian GNU/Linux 8 (jessie)"
NAME="Raspbian GNU/Linux"
VERSION_ID="8"
VERSION="8 (jessie)"
```

## 2) Install uv4l and avconv

### 2.1) Install uv4l for live video streaming (optional)

If you run into trouble, then follow [this tutorial][5]. If you don't do this, homecage should work but you won't be able to stream.

```
curl http://www.linux-projects.org/listing/uv4l_repo/lrkey.asc | sudo apt-key add -

# edit /etc/apt/sources.list
sudo pico /etc/apt/sources.list

# add the following line to /etc/apt/sources.list
deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/stretch stretch main

# update and install uv4l
sudo apt-get update
sudo apt-get install uv4l uv4l-raspicam
```

### 2.2) Install avconv to convert videos from .h264 to .mp4 (optional)

If you run into trouble, then see [this blog post][13]. If you don't do this, make sure you turn off the 'Convert video from h264 to mp4' option.

	sudo apt-get update
	sudo apt-get install libav-tools

Video files will be saved to `/home/pi/video`. If your going to save a lot of video, please [mount a usb key][12] and save videos there.



## 3) Clone the homecage repository

This will make a folder `homecage` in your root directory. You can always return to your root directory with `cd` or `cd ~`.

    # if you don't already have git installed
    sudo apt-get install git

	git clone --depth=1 https://github.com/cudmore/homecage.git

### 3.1) Either install python packages globally

	# if you don't already have pip installed (see troubleshooting)
	sudo apt-get install python-pip

	cd ~/homecage/homecage_app
	pip install -r requirements.txt

### 3.2) Or install in a virtual environment

Make a clean virtual environment that does not depend on current installed Python packages

	# if you don't already have pip installed (see troubleshooting)
	sudo apt-get install python-pip

	# install virtualenv if necessary (see troubleshooting)
	pip install virtualenv
	
	# make a folder to hold the virtual environment
	cd ~/homecage/homecage_app
	mkdir env	
	
	# either make a python 2 environment in the folder 'env'
	#virtualenv -p python2 --no-site-packages env
	
	# or make a python 3 environment in the folder 'env'
	virtualenv -p python3 --no-site-packages env

Activate the environment. Once activated, the command prompt will begin with '(env)'

	source env/bin/activate

Check your python version

	python -V
	
Make sure python command is running in the virtual environment

	which python

Install homecage_app dependencies

	cd ~/homecage/homecage_app
	pip install -r requirements.txt 

Run homecage_app.py

	cd ~/homecage/homecage_app
	python homecage_app.py

Browse to the homecage_app website

	http://[yourip]:5000
	
Exit virtual environment

	deactivate

## 4) Running homecage_app.py

	cd ~/homecage/homecage_app
	python homecage_app.py

Browse to the homecage_app website

	http://[yourip]:5000
	

## 5) Install DHT temperature sensor (optional)

If you run into trouble then go to [this tutorial][7]. If you don't do this, homecage should work but you won't be able to read the temperature and humidity.
    
    cd
    mkdir tmp
    cd tmp
    git clone https://github.com/adafruit/Adafruit_Python_DHT.git
    cd Adafruit_Python_DHT
    sudo python setup.py install

## 6) Start homecage_app at boot (optional)

Edit crontab

    crontab -e
    
Add the following line to the end of the file (make sure it is one line)

```
@reboot (sleep 10; cd /home/pi/homecage/homecage_app && /usr/bin/python /home/pi/homecage/homecage_app/homecage_app.py)
```

## 7) Done installing !!!

At this point you can interact with the homecage server through the [web][9] interface.

# Troubleshooting

As of May 21, 2018 pip 10 seems to be broken. Uninstall and then install pip 9

	# uninstall pip
	python -m pip uninstall pip
	
	# install pip 9
	python -m pip install -U "pip<10"
	
If virtualenv is not available (16.0.0)

	sudo /usr/bin/easy_install virtualenv

If you edit the config.json file it needs the correct sytax. Check the syntax with the following command. It will output the json if correct and an error otherwise.

	cat config.json | python -m json.tool


[0]: http://blog.cudmore.io/post/2017/11/22/raspian-stretch/
[1]: http://wiringpi.com/
[2]: http://flask.pocoo.org/
[3]: https://sourceforge.net/projects/raspberry-gpio-python/
[4]: https://github.com/adafruit/Adafruit_Python_DHT
[5]: https://www.linux-projects.org/uv4l/installation/
[7]: https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/software-install-updated
[8]: command-line.md
[9]: web-interface.md
[10]: rest-interface.md
[11]: http://blog.cudmore.io/post/2017/11/01/libav-for-ffmpeg/
[12]: http://blog.cudmore.io/post/2015/05/05/mounting-a-usb-drive-at-boot/
[13]: http://blog.cudmore.io/post/2017/11/01/libav-for-ffmpeg/
[14]: https://picamera.readthedocs.io/en/release-1.13/
[15]: https://libav.org/avconv.html
[putty]: https://www.putty.org/
