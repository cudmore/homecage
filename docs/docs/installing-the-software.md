## Overview: Required libraries

- [Wiring Pi][1] - Library that provides a command line interface to the GPIO pins. This should be installed by default.
- [GPIO][3] - Python library to control GPIO pins.
- [picamera][14] - Python library to control the camera.
- [flask][2] - A python web server.
- [Adafruit_DHT][4] - (optional) Python library to read from a DHT temperature and humidity sensor.
- [uv4l][5] - Command line tool for live video streaming to a web browser.
- [avconv][15] - Command line tool to convert video files.


## 1) Get a functioning Raspberry Pi

These instructions assume you have a functioning Raspberry Pi. To get started setting up a Pi from scratch, see our [setup intructions][0].

## 2) Clone the repository

This will make a folder `homecage` in your root directory. You can always return to your root directory with `cd`

    # if you don't already have git installed
    sudo apt-get install git

    git clone https://github.com/cudmore/homecage.git

## 3) Install python libraries

	# if you don't already have pip installed
	sudo apt-get install python-pip
	
	pip install rpi.gpio
	pip install flask

	# if you run into errors then try installing
	sudo apt-get install build-essential python-dev python-openssl
		
## 4) Install uv4l for live video streaming (optional)

If you run into trouble, then follow [this tutorial][5].

```
curl http://www.linux-projects.org/listing/uv4l_repo/lrkey.asc | sudo apt-key add -

# add the following line to /etc/apt/sources.list
# start editor with `sudo pico /etc/apt/sources.list`
deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/stretch stretch main

sudo apt-get update
sudo apt-get install uv4l uv4l-raspicam
```

Don't install `uv4l-server`

## 5) Install avconv to convert videos from .h264 to .mp4

If you run into trouble, then see [this blog post][13].

	sudo apt-get update
	sudo apt-get install libav-tools

Video files will be saved to `/home/pi/video`. This can be changed in the web server configuration file `homecage/homecage_app/config.json`. If your going to save a lot of video, please [mount a usb key][12] and save videos there.


## 6) Install DHT temperature sensor (optional)

If you run into trouble then go to [this tutorial][7].
    
    cd
    mkdir tmp
    cd tmp
    git clone https://github.com/adafruit/Adafruit_Python_DHT.git
    cd Adafruit_Python_DHT
    sudo python setup.py install

## 7) Start the web server at boot (optional)

Edit crontab

    crontab -e
    
Add the following line to the end of the file (make sure it is one line)

```
@reboot (sleep 10; cd /home/pi/homecage/homecage_app && /usr/bin/python /home/pi/homecage/homecage_app/homecage_app.py)
```

## Done installing !!!

At this point you can interact with the homecage either through the [web][9] or from the [command line][8].


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