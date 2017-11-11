Homecage requires the following libraries:

- [Wiring Pi][1] - Library that provides a command line interface to the GPIO pins. This should be installed by default.
- [GPIO][3] - Python library to control GPIO pins. This should be installed by default.
- [flask][2] - A python web server.
- [uv4l][5] - Library for live video streaming to a web browser
- [Adafruit_DHT][4] - (optional) Python library to read from a DHT temperature and humidity sensor.

## Installation

Clone the repository

    git clone https://github.com/cudmore/homecage.git

Make a virtual environment named `myenv` in `homecage/`

    cd homecage
    virtualenv myenv
       
Activate the environment

	source myenv/bin/deactivate
	 
Install python libraries

	pip install rpi.gpio
	pip install flask
	
To return to the normal command prompt

    deactivate
    
### uv4l for live video streaming

Install uv4l for live streaming (optional). Follow [this tutorial][5].

### Temperature sensor

Install DHT temperature sensor (optional)

    git clone https://github.com/adafruit/Adafruit_Python_DHT.git
    cd Adafruit_Python_DHT
    sudo python setup.py install

## Running the web server

```
cd
python homecage/homecage_app/homecage_app.py
```

## Configuring the web server

The server can be configured by editing the `homecage/homecage_app/config.json` file

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
