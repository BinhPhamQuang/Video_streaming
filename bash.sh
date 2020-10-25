#!/bin/sh
python Server.py 1025
python ClientLauncher.py 172.17.2.221 1025 5008 video.mjpeg
