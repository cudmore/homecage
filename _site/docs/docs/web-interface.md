
<IMG SRC="../img/web-interface-minimal.png" width=600 style="border:1px solid black">

## Running the web server

Login to the Pi

	ssh pi@[your_ip]
	
Where [your_ip] is the IP address of your Pi.

At a command prompt, type:

```
cd
cd homecage/homecage_app
python homecage_app.py
```
    
Once `homecage_app.py` is running you can access the web server in a browser with the address:

    http:[your_ip]:5000
    
Where [your_ip] is the IP address of your Pi.

To stop the homecage web server, in the command prompt use keyboard `ctrl+c`

## Viewing saved videos

Click the hard-drive icon to view saved video files.

## Setting options

### In the web interface

Expand the `options` tab to set parameters of homecage. Each option will apply to the current session. Use `save options` to permanaently save the options. Load the default options again with 'Load Default Options'.

<IMG SRC="../img/web-options.png" width=325 style="border:1px solid black">


### On the Pi

The homecage options can be configured by editing the [homecage/homecage_app/config.json][1] file.

    cd
    pico homecage/homecage_app/config.json 

The default file is:

```json
{
    "hardware": {
        "irLightPin": 7, 
        "whiteLightPin": 8,
        "temperatureSensor": 9, 
        "temperatureInterval": 20 
    }, 
    "lights": {
        "controlLights": true, 
        "sunset": 18, 
        "sunrise": 6
    }, 
    "video": {
        "fileDuration": 10, 
        "converttomp4": true, 
        "fps": 30, 
        "resolution": [
            1024, 
            768
        ],
        "captureStill": true, 
        "stillInterval": 2 
    }, 
    "stream": {
        "streamResolution": [
            1024, 
            768
        ]
    }
}
``` 

[1]: https://github.com/cudmore/homecage/blob/master/homecage_app/config.json