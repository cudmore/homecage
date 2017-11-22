Homecage requires the following libraries:

- [Wiring Pi][1] - Library that provides a command line interface to the GPIO pins. This should be installed by default.
- [GPIO][3] - Python library to control GPIO pins. This should be installed by default.
- [flask][2] - A python web server.
- [uv4l][5] - Library for live video streaming to a web browser
- [Adafruit_DHT][4] - (optional) Python library to read from a DHT temperature and humidity sensor.

## Installation

### Clone the repository

This will make a folder `homecage` in your root directory. You can always return to your root directory with `cd`

    git clone https://github.com/cudmore/homecage.git

### Install python libraries

	# if you don't already have pip installed
	sudo apt-get install python-pip
	
	pip install rpi.gpio
	pip install flask

	# if you run into errors then try installing
	sudo apt-get install build-essential python-dev python-openssl
		
### Install DHT temperature sensor (optional)

If you run into trouble then go to [this tutorial][7].

    # if you don't already have git installed
    sudo apt-get install git
    
    mkdir tmp
    cd tmp
    git clone https://github.com/adafruit/Adafruit_Python_DHT.git
    cd Adafruit_Python_DHT
    sudo python setup.py install

### uv4l for live video streaming

Install uv4l for live streaming (optional). If you run into trouble, then follow [this tutorial][5].

```
curl http://www.linux-projects.org/listing/uv4l_repo/lrkey.asc | sudo apt-key add -
/etc/apt/sources.list

# add the following line to /etc/apt/sources.list
# start editor with `sudo /etc/apt/sources.list`
deb http://www.linux-projects.org/listing/uv4l_repo/raspbian/ jessie main

sudo apt-get update
sudo apt-get install uv4l uv4l-raspicam

# DO NOT INSTALL `sudo apt-get install uv4l-raspicam-extras`
```

# Done installing

At this point you can interact with the homecage either through the command line or the web interface.

## Homecage command line

```
cd
cd homecage
./help
```

Will give you this. Start typing away...

```
Status
    status - check the status
 Video Recording
    record start
    record stop
 Video Streaming
    stream start
    stream stop
 IR Light
    light ir on
    light ir off
 White Light
    light white on
    light white off
 Online Manual
    http://blog.cudmore.io/homecage
```

## Homecage webserver

Run the homecage web server with

```
cd
cd homecage/homecage_app
python homecage_app.py
```

Once `homecage_app.py` is running you can open the web server in a browser with the address:

    http:[your_ip]:5000
    
Where [your_ip] is the IP address of your Pi.

To stop the homecage webserver, use keyboard `ctrl+c`

## Configuring the web server

The server can be configured by editing the `homecage/homecage_app/config.json` file.

    cd
    pico homecage/homecage_app/config.json 

The default file is:

```json
{
	"hardware":{
		"irLightPin": 7,
		"whiteLightPin": 8,
		"temperatureSensor": 9
	},
	"lights":{
		"sunrise": 6,
		"sunset": 18
	},
	"video":{
		"fps": 30,
		"resolution": [1024,768],
		"fileDuration": 6,
		"captureStill": true,
		"stillInterval": 2
	},
	"stream": {
		"streamResolution": [1024,768]
	}
}
```

## Converting h264 files to mp4

The Raspberry camera saves .h264 video files. This format is very efficient and creates  small files (10 MB per 5 minutes) but does require conversion to mp4 to impose a time.

See this [blog post][6]

[1]: http://wiringpi.com/
[2]: http://flask.pocoo.org/
[3]: https://sourceforge.net/projects/raspberry-gpio-python/
[4]: https://github.com/adafruit/Adafruit_Python_DHT
[5]: https://www.linux-projects.org/uv4l/installation/
[6]: http://blog.cudmore.io/post/2017/11/01/libav-for-ffmpeg/
[7]: https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/software-install-updated