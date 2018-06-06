# Install homecage

We will assume you have a functioning Raspberry Pi. To get started setting up a Pi from scratch, see our [setup intructions][0]. We will also assume you are logged in to the Pi using terminal on OSX or [Putty][putty] on Windows.

## 1) Check your system

Homecage runs best on a Raspberry 2/3 and Debian Stretch. **Do not run it on Raspberry Model B, it is too slow**.

Check which version of the Raspberry Pi you have.

```
#at a command prompt, type
cat /proc/device-tree/model

#you should get something like this
Raspberry Pi 3 Model B Rev 1.2
```

Check which version of the Debian operating system you have. You should use Debian Stretch if possible

```
#at a command prompt, type
cat /etc/os-release

#you should get something like this
PRETTY_NAME="Raspbian GNU/Linux 9 (stretch)"
NAME="Raspbian GNU/Linux"
VERSION_ID="9"
VERSION="9 (stretch)"
```


## 2) Clone the homecage repository

This will make a folder `homecage` in your root directory. You can always return to your root directory with `cd`.

    # if you don't already have git installed
    sudo apt-get install git

	git clone --depth=1 https://github.com/cudmore/homecage.git

## 3) Install homecage with our install script

	# at a command prompt, type
	cd homecage/homecage_app
	./install.sh
	
If everything goes well, all the software should be ready to go. Point your browser to

	http://[your_ip]:5000
	
## 3.1) Or manually install python packages globally

	# if you don't already have pip installed (see troubleshooting)
	sudo apt-get install python-pip

	cd ~/homecage/homecage_app
	pip install -r requirements.txt

Run homecage_app.py

	cd ~/homecage/homecage_app
	python homecage_app.py

Browse to the homecage_app website

	http://[yourip]:5000

## 3.2) Or manually install in a virtual environment

Installing into a Python virtual environment is a good idea as it isolates the installation of home cage from your system.

Make a clean virtual environment that does not depend on current installed Python packages.

	# if you don't already have pip installed (see troubleshooting)
	sudo apt-get install python-pip

	# install virtualenv if necessary (see troubleshooting)
	pip install virtualenv
	
	# if you still can't use virtualenv, then install like this
	sudo /usr/bin/easy_install virtualenv
	
	# make a folder to hold the virtual environment
	cd ~/homecage
	mkdir env	
	
	# either make a python 2 environment in the folder 'env'
	#virtualenv -p python2 --no-site-packages env
	
	# or make a python 3 environment in the folder 'env'
	virtualenv -p python3 --no-site-packages env

Activate the environment. Once activated, the command prompt will begin with '(env)'

	source env/bin/activate

Install homecage_app dependencies

	cd ~/homecage/homecage_app
	pip install -r requirements.txt 

Run homecage_app.py

	cd ~/homecage/homecage_app
	python homecage_app.py

Browse to the homecage_app website

	http://[yourip]:5000
	
To exit the virtual Python environment

	deactivate

## 4) Manually install uv4l and avconv

Homecage uses uv4l to stream video to the web and avconv to convert h264 video files to mp4.

### 4.1) Manually install uv4l for live video streaming (optional)

If you run into trouble, then follow [this tutorial][5]. If you don't do this, homecage will work but you won't be able to stream.

Because uv4l is complicated, **this will only work in Raspian Stretch**
```
# at a comman prompt, type
curl http://www.linux-projects.org/listing/uv4l_repo/lrkey.asc | sudo apt-key add -

# edit /etc/apt/sources.list
sudo pico /etc/apt/sources.list

# add the following line to /etc/apt/sources.list
deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/stretch stretch main

# update and install uv4l
sudo apt-get update
sudo apt-get install uv4l uv4l-server uv4l-raspicam
```

### 4.2) Manually install avconv to convert videos from .h264 to .mp4 (optional)

If you run into trouble, then see [this blog post][13]. If you don't do this, make sure you turn off the 'Convert video from h264 to mp4' option.

	sudo apt-get update
	sudo apt-get install libav-tools

Video files will be saved to `/home/pi/video`. If your going to save a lot of video, please [mount a usb key][12] and save videos there.


[0]: http://blog.cudmore.io/post/2017/11/22/raspian-stretch/
[1]: http://wiringpi.com/
[2]: http://flask.pocoo.org/
[3]: https://sourceforge.net/projects/raspberry-gpio-python/
[4]: https://github.com/adafruit/Adafruit_Python_DHT
[5]: https://www.linux-projects.org/uv4l/installation/
[8]: command-line.md
[9]: web-interface.md
[10]: rest-interface.md
[troubleshooting]: troubleshooting.md
[11]: http://blog.cudmore.io/post/2017/11/01/libav-for-ffmpeg/
[12]: http://blog.cudmore.io/post/2015/05/05/mounting-a-usb-drive-at-boot/
[13]: http://blog.cudmore.io/post/2017/11/01/libav-for-ffmpeg/
[14]: https://picamera.readthedocs.io/en/release-1.13/
[15]: https://libav.org/avconv.html
[putty]: https://www.putty.org/
