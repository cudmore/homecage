
## Change Log

#### 20180307

Added script to convert all .h264 to .mp4 (without replacement), uses avconv. See homecage/convert for script and dev notes for a copy of the script.


#### 20180202

Added code to command line to convert .h264 to .mp4 at end of video recorindg.

See `video.py`:

```
print '    Converting from .h264 to .mp4 with convert_video.sh (avconv)'
cmd = './convert_video.sh ' + thisVideoFile + ' ' + str(fps)
child = subprocess.Popen(cmd, shell=True)
out, err = child.communicate()
```

Be careful as avconv uses `-framerate` and not `-r` as is with ffmpeg. See `convert_video.sh`:

```
cmd="avconv -loglevel error -framerate $2 -i $1 -vcodec copy -r $2 $dstfile"
echo "    "$cmd
```

#### 20171201

 - Added dialog when stopping video
 - added 'videolist.html' page to display list of video and play on click !
 - now converting .h264 to .mp4
    - added to config.json as 'config.video.converttomp4: true'
    - added bash script convert_video.sh, to do conversion
    - call bash script when video is done (in thread)
    - added documentation to install avconv
 - now saving into date folder

#### 20171111

 - finish index.html interface, mostly adding interface to change self.config
 - split self.config (from config.json) and self.status (runtime variables)
 - add in dht sensor code
 - add in white and ir sensor code

#### 20171101

 - Started rewriting homecage to include (i) command line control, (ii) web interface. Previous version required manually running both lights and video as separate processes using `sreen`.
 
## mkDocs

We use [mkdocs][mkdocs] to generate the documentation website from markdown files.

Install

    pip install mkdocs
    
    # we are using the material theme
    pip install mkdocs-material
    
Serve locally

    cd
    cd homecage/docs
    mkdocs serve
    
Push to github

    cd
    cd homecage/docs
    mkdocs gh-deploy --clean 

## uv4l

uv4l is what we use to stream live video.

20171120 - Problem was that if streaming was on and we tried to stop it while there was still an opened browser window we would get an orphaned `<defunct>` process that can't actually be kill(ed). This was mucking up any future interaciton as `stream`, `record`, and `status` thought there was still a uv4l process.

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

Which eventually led to this

```
# get uv4l PID
PID = pgrep uv4l
# kill all processes in the same group, this includes children
# kills original and does NOT leave a `<defunct>` uv4l !
sudo kill -- -PID
```

#### Remove uv4l-raspicam-extras

    sudo apt-get remove uv4l-raspicam-extras
    
 
[mkdocs]: http://www.mkdocs.org/

