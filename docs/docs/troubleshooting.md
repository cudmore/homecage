## Video recording

Manually capture a single image

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
	Version 1.9.12 built on Aug 15 2017


Run uv4l by hand

```
uv4l --driver raspicam --auto-video_nr --encoding h264 --width 640 --height 480 --enable-server on
```

Browse the live stream at

```
http://[IP]:8080
```

Stop uv4l (make sure all browser windows are closed)

```
sudo pkill uv4l
```

## Converting h264 to mp4

Install ffmpeg on a mac

- install xcode
- activate xcode command line tools
- install homebrew
- run at command prompt

    brew install ffmpeg --with-libvpx
    
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
   avconv -i "$file" -r $fps -vcodec copy "$file.mp4"
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
