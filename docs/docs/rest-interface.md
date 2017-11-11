The homecage server will respond to the following REST calls.


## Server Status: 

Get runtime status of server

    /status

Get user configured options

    /params 
    
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

    /set/fps/&lt;int:value> 
    /set/fileDuration/&lt;int:value> 
