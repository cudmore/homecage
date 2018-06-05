## Video recording

Manually capture a single image using built in raspistill. The following command will take an image and save it into test.jpg

```
raspistill -o test.jpg
```

## Video streaming

Check version of uv4l

	# type
	uv4l -i
	
	# returns
	Userspace Video4Linux
	Copyright (C) Luca Risolia <luca.risolia@linux-projects.org>
	Version 1.9.16 built on Jan 28 2018


Run uv4l by hand

```
uv4l --driver raspicam --auto-video_nr --encoding h264 --width 640 --height 480 --enable-server on
```

Browse the live stream at

```
http://[your_ip]:8080
```

Stop uv4l (make sure all browser windows are closed)

```
sudo pkill uv4l
```

## Problems with pip

Sometimes pip version 10 seems to be broken. Uninstall and then install pip version 9

	# uninstall pip
	python -m pip uninstall pip
	
	# install pip 9
	python -m pip install -U "pip<10"
	
## Problems with virtualenv

If virtualenv is not available (16.0.0)

	sudo /usr/bin/easy_install virtualenv

## Manually configuring config.json

If you edit the config.json file it needs the correct sytax. Check the syntax with the following command. It will output the json if correct and an error otherwise.

	cat config.json | python -m json.tool

## socket.error: [Errno 98] Address already in use

Sometimes you will get an error when you run `python homecage_app.py`. This means there is already a prcoess using the web socket, usually :5000

Use `ps -aux | grep homecage_app` to find the process and kill it

```
# type this
ps -aux | grep homecage_app

# will yield something like this
pi       12445  0.1  2.2  41572 20204 pts/2    Sl   17:14   0:04 python homecage_app.py
pi       12553  2.3  2.3  51032 20328 pts/2    Sl   17:50   0:08 /usr/bin/python homecage_app.py
pi       12606  0.0  0.3   6080  3036 pts/2    S+   17:57   0:00 grep --color=auto homecage_app

#Using those 5 digit numbers, kill all homecage_app processes
kill -9 12553
kill -9 12445

## Converting h264 to mp4

We use avconv to convert h264 to mp4 and then avprobe to check the parameters of the output mp4 file.

Check the version of avconv

	# type
	avconv -version

	# returns
	ffmpeg version 3.2.9-1~deb9u1 Copyright (c) 2000-2017 the FFmpeg developers
	built with gcc 6.3.0 (Raspbian 6.3.0-18+rpi1) 20170516
	configuration: --prefix=/usr --extra-version='1~deb9u1' --toolchain=hardened --libdir=/usr/lib/arm-linux-gnueabihf --incdir=/usr/include/arm-linux-gnueabihf --enable-gpl --disable-stripping --enable-avresample --enable-avisynth --enable-gnutls --enable-ladspa --enable-libass --enable-libbluray --enable-libbs2b --enable-libcaca --enable-libcdio --enable-libebur128 --enable-libflite --enable-libfontconfig --enable-libfreetype --enable-libfribidi --enable-libgme --enable-libgsm --enable-libmp3lame --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librubberband --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libspeex --enable-libssh --enable-libtheora --enable-libtwolame --enable-libvorbis --enable-libvpx --enable-libwavpack --enable-libwebp --enable-libx265 --enable-libxvid --enable-libzmq --enable-libzvbi --enable-omx --enable-openal --enable-opengl --enable-sdl2 --enable-libdc1394 --enable-libiec61883 --enable-chromaprint --enable-frei0r --enable-libopencv --enable-libx264 --enable-shared
	libavutil      55. 34.101 / 55. 34.101
	libavcodec     57. 64.101 / 57. 64.101
	libavformat    57. 56.101 / 57. 56.101
	libavdevice    57.  1.100 / 57.  1.100
	libavfilter     6. 65.100 /  6. 65.100
	libavresample   3.  1.  0 /  3.  1.  0
	libswscale      4.  2.100 /  4.  2.100
	libswresample   2.  3.100 /  2.  3.100
	libpostproc    54.  1.100 / 54.  1.100


Check the version of avprobe which is used to read converted .mp4 files to make sure we get the correct parameters. It seems the Jessie version has frames-per-second in avg_frame_rate and the Stretch version has it in r_frame_rate (or maybe the other way around). Thus, we are hard coding fps based on user options. There is a fear that the call to convert h264 to mp4 could change in the future and we might get fps wrong.  Please verify your frames-per-second are as expected.

	avprobe -v

Raspian Jessie gives

avprobe version 11.12-6:11.12-1~deb8u1+rpi1, Copyright (c) 2007-2018 the Libav developers
  built on Feb 21 2018 04:51:45 with gcc 4.9.2 (Raspbian 4.9.2-10+deb8u1)

Raspian Stetch gives

ffprobe version 3.2.9-1~deb9u1 Copyright (c) 2007-2017 the FFmpeg developers
  built with gcc 6.3.0 (Raspbian 6.3.0-18+rpi1) 20170516

## Manually converting h264 files to mp4

The Raspberry camera saves .h264 video files. This format is very efficient and creates small files (10 MB per 5 minutes) but does require conversion to mp4 to impose a time.

### Using avconv

This will convert all .h264 files in **a folder** into .mp4 files with 15 fps.

```bash
#!/bin/bash
fps=15
for file in *.h264 ; do
   filename="${file%.*}"
   echo $filename
   avconv -framerate $fps -i "$file" -r -vcodec copy "$file.mp4"
   sleep 3
done
```

### Using ffmpeg

This will convert all .h264 files in **a folder** into .mp4 files with 15 fps.

```bash
#!/bin/bash
fps=15
for file in *.h264 ; do
   filename="${file%.*}"
   echo $filename
   ffmpeg -r $fps -i "$file" -vcodec copy "$file.mp4"
   sleep 3
done
```

This will recursively convert all .h264 files in a folder and **all of its subfolders** into .mp4 files.

```bash
#!/bin/bash
fps=15
IFS=$'\n'
for file in $(find . -iname '*.h264') ; do
	#printf '%s\n' "$file"
	ffmpeg -r $fps -i "$file" -vcodec copy "$file.mp4"
done
```

See [this blog post][6]




[6]: http://blog.cudmore.io/post/2017/11/01/libav-for-ffmpeg/
