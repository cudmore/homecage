
## git

### git dev branch

	# checkout a branch 'dev'
	git checkout dev
	
	# see all branches
	git branch
	
	# commit ('dev' is implicit)
	git commit -a -m 'test'
	
	# CRITICAL, push to 'dev'
	git push -u origin dev

	# merge (go into master and fast-forward merge dev)
	git checkout master
	git merge dev
	
### git master branch

Set up password

	git config --global credential.helper 'cache --timeout=10000000'
	
Clone

	git clone https://github.com/cudmore/homecage.git
	
Pull

	git pull

Commit all changes. Do this a second time to see untracked files

	git commit -a -m 'test'

Add files

	git add <filename>
	
Push

	git push -u origin master
	
## Install in virtual env

Make a clean virtual environment that does not depend on current installed packages

	# make a folder to hold your virtual environment
	mkdir env
		
	# make a python 2 environment
	#virtualenv -p python2 --no-site-packages env
	
	# make a python 3 environment
	virtualenv -p python3 --no-site-packages env

Activate the environment

	source env/bin/activate

Check your python version

	python -V
	
Make sure python command is running in the virtual environment

	which python

Install homecage_app dependencies

	pip install -r requirements.txt 

Run homecage_app.py

	python homecage_app.py

Browse to the homecage_App website

	http://[yourip]:5000
	
Exit virtual environment

	deactivate
	
## mkDocs

We use [mkdocs][mkdocs] to generate the documentation website from markdown files. On the Raspberry, mkdocs will only install into Python 3.x

Install

    pip install mkdocs
    
    # we are using the material theme
    pip install mkdocs-material
    
Serve locally

    cd
    cd homecage/docs
    mkdocs serve
    
    # or if logged in to a remote pi, serve using the pi ip
    mkdocs serve -a 192.168.1.3:8000
    
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
    
## nginx+uwsgi+flask

Follow [this](https://iotbytes.wordpress.com/python-flask-web-application-on-raspberry-pi-with-nginx-and-uwsgi/).

and [my blog post](http://blog.cudmore.io/post/2018/01/14/nginx+flask+uwsgi+rest/)

- install nginx and uwsgi

```
sudo apt-get install nginx
sudo pip install uwsgi
```

- start and stop nginx

    sudo service nginx start

- change group (not user) of folder

    sudo chown -R pi:www-data /home/pi/homecage/homecage_app

- not sure if this is necessary but won't hurt and should not break

	sudo usermod -aG www-data pi

- contents of homecage/homecage_app/uwsgi_config.ini

Because we are using GPIO callbacks, we can't have more than 1 process and 1 thread.

```
[uwsgi]

chdir = /home/pi/homecage/homecage_app
module = homecage_app:app

master = true
processes = 1
threads = 1

#uid = www-data 
#gid = www-data

#uid = pi 
#gid = pi

socket = /tmp/homecage_app.sock
chmod-socket = 660
vacuum = true

die-on-term = true
```

- run uwsgi and check it creates /tmp/homecage_app.sock

    uwsgi --ini /home/pi/homecage/homecage_app/uwsgi_config.ini

- make uwsgi run at boot

    sudo pico /etc/rc.local
    
    #append to end of file before 'exit 0'
    /usr/local/bin/uwsgi --ini /home/pi/homecage/homecage_app/uwsgi_config.ini --uid pi --gid www-data --daemonize /var/log/uwsgi.log

- configure nginx routing

    # remove default
    sudo rm /etc/nginx/sites-enabled/default

	# create our own
	sudo pico /etc/nginx/sites-available/homecage_app_proxy
	
	# make `homecage_app_proxy` look like this

```
server {
  listen 80;
  server_name localhost;

  location / {
    include uwsgi_params;
    uwsgi_pass unix:///tmp/homecage_app.sock;
  }
}
```

- link `homecage_app_proxy` into `sites-enabled` folder

    sudo ln -s /etc/nginx/sites-available/homecage_app_proxy /etc/nginx/sites-enabled
    
- restart nginx

    sudo service nginx restart

- good to go at http://[IP]

## Change Log

#### 20171111

 - finish index.html interface, mostly adding interface to change self.config
 - split self.config (from config.json) and self.status (runtime variables)
 - add in dht sensor code
 - add in white and ir sensor code

#### 20171201

 - Added dialog when stopping video
 - added 'videolist.html' page to display list of video and play on click !
 - now converting .h264 to .mp4
    - added to config.json
    - added bash script convert_video.sh
    - call bash script when video is done (in thread)
    - added documentation to install avconv
 - now saving into date folder
 

#### 20180520

- Added 3rd component to trigger recording from scope, this includes
  
    - 'Arm' state to continuously record video into a memory loop
    - On trigger in, save pre-triggered video and start saving video for a trial
    - On frame pin, watermark video with frame number
    - Added 'scope' section to config.json

- Rewrote install documentation to include virtualenv
- Started using git from Pi, can now synch with homecage on github, and push mkdocs !!!
- To Do

    - Fix background text on frame watermark
    - Save trial information to a trial .txt file
    - Revamp .log to include trial information
    
#### 20180520

	- Added checks in bash scripts to exit nicely if uv4l and avconv are not installed
	- Added script for avprobe (so we can fail niely when not installed)
	- Added option to record x number of files (set to one when on scope and using triggerIn)

#### 20180601

	- now using logger throughout (no more print)
	- removed use of avprobe to get video file params, just report file size in file browser
	- now using systemctl and homecage.service to easily start, stop, and run at boot
	- ./install.sh 
	- finalized html forms to set params. be careful of conversions between javascript, python, and json dictionaries. For example unexpected conversions between float, int, string
	- starting to think about running nginx-	

### Setup

homecage2 is b8:27:eb:88:33:07
cudmore_pib is b8:27:eb:aa:51:6d

[mkdocs]: http://www.mkdocs.org/
