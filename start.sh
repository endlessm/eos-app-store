#!/bin/bash

export DISPLAY=:0

export ENDLESS_SHARED_DATA_DIR=/home/endlessm/checkout/eos-desktop

nohup python src/endless_os_desktop.py > console.log 2>&1 &
#echo "kill -9 $!" > kill.sh
#chmod +x kill.sh
