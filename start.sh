#!/bin/bash

export DISPLAY=:0

nohup python src/endless_os_desktop.py > console.log 2>&1 &
#echo "kill -9 $!" > kill.sh
#chmod +x kill.sh
