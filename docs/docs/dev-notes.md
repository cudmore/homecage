
## mkDocs

Serve locally

    mkdocs serve
    
Push to github

    cd homecage/docs
    mkdocs gh-deploy --clean 

## uv4l

20171120 - Problem was that if streaming was on and we tried to stop it while there was still an opened browser window we would get an orphaned `<defunct>` process that can't actually be kill(ed). This was mucking up any future interaciton as `stream`, `record`, and `status` thought there was still a uv4l process.

Fixing this by using `uv4l-raspicam-extras`

    sudo apt-get install uv4l-raspicam-extras
 
We now start/stop the stream with

    sudo service uv4l_raspicam start
    sudo service uv4l_raspicam stop

When we start/stop like this we are now using a config file `/etc/uv4l/uv4l-raspicam.conf`

    sudo pico /etc/uv4l/uv4l-raspicam.conf
    
And need to knock down the default stream resolution so we get the full field-of-view. Do this by uncommenting and specifying width and height in `/etc/uv4l/uv4l-raspicam.conf`.

```
##################################
# raspicam driver options
##################################

encoding = mjpeg
width = 640
height = 480
framerate = 30
#custom-sensor-config = 2
```

#### Sent this to uv4l people

```
Hi there, great product and the best streaming I have ever seen.

I am running uv4l on a Raspberry Pi (Jessie) and it is working very well.
One problem is if I kill the stream with `sudo pkill uv4l` while there is
a browser window open (that is viewing the stream) I end up with a <defunct>
uv4l process that I can't seem to kill?

Can you suggest a server option I could use to stop this behavior?
I want to `sudo pkill uv4l` from the pi while some remote user still
has a stream window open in the browser? I've looked through the server
options and don't really know what I am looking for?

Thanks again for uv4l

p.s. Can you suggest an online forum for such questions?
```
Answer was to kill child processes first. Get child processes of PID with `pstree -p PID'

When browser window is streaming

```
uv4l(2345)─┬─{HCEC Notify}(2351)
           ├─{HDispmanx Notif}(2349)
           ├─{HTV Notify}(2350)
           ├─{VCHIQ completio}(2348)
           ├─{uv4l}(2346)
           ├─{uv4l}(2347)
           ├─{uv4l}(2360)
           ├─{uv4l}(2361)
           ├─{uv4l}(2362)
           ├─{uv4l}(2385)
           ├─{uv4l}(2386)
           ├─{uv4l}(2387)
           ├─{uv4l}(2389)
           ├─{uv4l}(2393)
           ├─{uv4l}(2394)
           ├─{vc.ril.camera}(2390)
           ├─{vc.ril.image_en}(2392)
           └─{vc.ril.video_re}(2391)
```

When it is not streaming

```
uv4l(2345)─┬─{HCEC Notify}(2351)
           ├─{HDispmanx Notif}(2349)
           ├─{HTV Notify}(2350)
           ├─{VCHIQ completio}(2348)
           ├─{uv4l}(2346)
           ├─{uv4l}(2347)
           ├─{uv4l}(2360)
           ├─{uv4l}(2361)
           ├─{uv4l}(2362)
           ├─{uv4l}(2385)
           ├─{uv4l}(2386)
           └─{uv4l}(2387)
```

#### Progress on killing while browser window is open

```
# get uv4l PID
PID = pgrep uv4l
# kill all processes in the same group, this includes children
sudo kill -- -PID
# kills original and does NOT leave a `<defunct>` uv4l !
# once we do this we need to use `restart`
sudo service uv4l_raspicam restart
# uninstall the raspberry-util and revert to original command line calls
# use this technique to kill
```

#### remove uv4l-raspicam-extras

    sudo apt-get remove uv4l-raspicam-extras
    
## ToDo

### 20171111

 - finish index.html interface, mostly adding interface to change self.config
 - split self.config (from config.json) and self.status (runtime variables)
 - add in dht sensor code
 - add in white and ir sensor code

