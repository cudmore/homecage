Assorted setup and utility scripts

## startup_mailer.py - required gmail_auth.secret
## startup_tweeter.py - requires twitter_auth.secret

Contents of `gmail_auth.secret,json`

```
{
	"gmail_user": "your_user_name@gmail.com",
	"gmail_password": "your_password"
}
```

## convert_video.sh

bash script called by home.py to convert .h264 video to .mp4, uses system wide avconv

## stream

bash script called by home.py to stream video using system wide uv4l

## homecage
## homecage_service.sh
## homecage.service

bash scripts and service file used to install and run systemctl homecage.service

## uwsgi_config.ini

Essential file to run homecage_app.py web server behind nginx+uwsgi


