## Converting h264 files to mp4

The Raspberry camera saves .h264 video files. This format is very efficient and creates small files (10 MB per 5 minutes) but does require conversion to mp4 to impose a time.

```bash
#!/bin/bash
for file in *.h264 ; do
   filename="${file%.*}"
   echo $filename
   ffmpeg -r 15 -i "$file" -vcodec copy "mp4/$file.mp4"
   sleep 3
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
