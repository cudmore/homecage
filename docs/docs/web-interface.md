
<IMG SRC="../img/web-interface-minimal.png" width=600>

## Running the web server

At a command prompt, type:

```
cd
cd homecage/homecage_app
python homecage_app.py
```
    
Once `homecage_app.py` is running you can access the web server in a browser with the address:

    http:[your_ip]:5000
    
Where [your_ip] is the IP address of your Pi.

To stop the homecage web server, use keyboard `ctrl+c`
    
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
