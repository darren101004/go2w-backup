#!/bin/bash

WAV="Tiger.wav"

aplay -D hw:1,0 $WAV &   # chạy background
pid=$!
wait $pid                # chờ tới khi aplay kết thúc
echo "Playback done"