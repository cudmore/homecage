Once the homecage server is running, it will respond to the following [REST][rest] end points. Simply put, the REST interface allows you to control a Raspberry Pi camera from a web-browser.

With this, it is relatively simple to write your own code to control a Raspberry Pi running the homecage server. You could do this from Python, Javascript, Matlab, or Igor. For example, we (and now you) are using this interface for both the [web][web] and [video wall][videowall] interfaces.

You can try this out by entering the following web addresses into your browser:

	http://[your_pi_ip]:5000/status
	
And you should get something like this:

```
{
  "environment": {
    "humidity": 1.0,
    "temperature": 28.29
  },
  "lights": {
    "irLED": false,
    "whiteLED": false
  },
  "server": {
    "lastResponse": "",
    "state": "idle"
  },
  "system": {
    "cpuTemperature": "48.3",
    "date": "2018-05-21",
    "gbRemaining": "7.70",
    "gbSize": "14.48",
    "hostname": "pi3",
    "ip": "192.168.1.3",
    "time": "13:24:23"
  },
  "trial": {
    "startTimeSeconds": null,
    "timeRemaining": null
  }
}
```


## Server Status: 

Get runtime status of server

    /status

Get user configured options

    /config 
    
## Record

Start and stop video recording

    /record/1 
    /record/0 

## Stream

Start and stop video streaming

    /stream/1 
    /stream/0 

## Lights

Turn lights on and off

    /irLED/1 
    /irLED/0 
    /whiteLED/1 
    /whiteLED/0 

## Images 

    /lastimage 

## Set user options

    /set/fps/<int:value> 
    /set/fileDuration/<int:value> 

## Simulate a scope

	/simulate/triggerin
	/simulate/frame
	/simulate/stop

[rest]: https://en.wikipedia.org/wiki/Representational_state_transfer
[web]: web-interface.md
[videowall]: videowall.md

