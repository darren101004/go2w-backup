sudo pkill  mediamtx
./mediamtx &
ffmpeg -f v4l2 -i /dev/video2 \
    -c:v libx264 -preset ultrafast -tune zerolatency \
    -f rtsp rtsp://0.0.0.0:8554/mystream