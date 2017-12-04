## Converting h264 files to mp4

The Raspberry camera saves .h264 video files. This format is very efficient and creates small files (10 MB per 5 minutes) but does require conversion to mp4 to impose a time.

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
fps=15
IFS=$'\n'
for file in $(find . -iname '*.h264') ; do
	#printf '%s\n' "$file"
	ffmpeg -r $fps -i "$file" -vcodec copy "$file.mp4"
done
```

See [this blog post][6]

## Troubleshoot video recording

Capture a single image

```
raspistill -o test.jpg
```

## Troubleshoot video streaming

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

[6]: http://blog.cudmore.io/post/2017/11/01/libav-for-ffmpeg/
