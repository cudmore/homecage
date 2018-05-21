
<IMG SRC="../img/web-interface-minimal.png" width=600 style="border:1px solid black">

## Running the web server

Login to the Pi

	ssh pi@[your_pi_ip]
	
Where [your_pi_ip] is the IP address of your Pi.

At a command prompt, type:

```
cd
cd homecage/homecage_app
python homecage_app.py
```
    
Once `homecage_app.py` is running you can access the web server in a browser with the address:

    http:[your_pi_ip]:5000
    
Where [your_pi_ip] is the IP address of your Pi.

To stop the homecage web server, in the command prompt use keyboard `ctrl+c`

## Viewing saved videos

Click the hard-drive icon to view saved video files.

## Setting options

### In the web interface

Expand the `options` tab to set parameters of homecage. Use `save options` to permanaently save the options. Load the default options again with 'Load Default Options'.

<IMG SRC="../img/web-options.png" width=325 style="border:1px solid black">

Videos are saved in the .h264 format and need to be converted to .mp4 which can be slow. Turn off 'Convert video from h264 to mp4' and convert manually at the end of an experiment.

### On the Pi

Most of the options can be changed and saved using the web interface. The  options can also be configured manually by editing the [homecage/homecage_app/config.json][1] file.

    cd ~/homecage/homecage_app
    pico config.json 

If you edit the config.json file it needs the correct sytax. Without the correct syntax `python homecage_app.py` **will** fail. Check the syntax with the following command. It will output the json if correct and an error otherwise.

	cat config.json | python -m json.tool

The default [config.json][1] file is:

```json
{
    "hardware": {
        "whiteLightPin": 2, 
        "irLightPin": 3, 
        "readtemperature": true, 
        "temperatureInterval": 20, 
        "temperatureSensor": 4
    }, 
    "lights": {
        "auto": false, 
        "sunset": 18, 
        "sunrise": 6
    }, 
    "video": {
        "fileDuration": 5, 
        "converttomp4": true, 
        "captureStill": true, 
        "savepath": "/home/pi/video", 
        "fps": 30, 
        "stillInterval": 2, 
        "resolution": "1024,768"
    }, 
    "stream": {
        "resolution": "640,480"
    }, 
    "scope": {
        "autoArm": false, 
        "bufferSeconds": 5, 
        "frameIn": {
            "enabled": true, 
            "pin": 18, 
            "polarity": "rising"
        }, 
        "triggerIn": {
            "enabled": true, 
            "pin": 20, 
            "polarity": "rising"
        }, 
        "triggerOut": {
            "enabled": true, 
            "pin": 31, 
            "polarity": "rising"
        }
    }
}
``` 


[1]: https://github.com/cudmore/homecage/blob/master/homecage_app/config.json