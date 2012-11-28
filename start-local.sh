#!/bin/bash

./kill.sh

cp ~/checkout/eos-config/etc/endlessm/desktop.en_US ~/.endlessm/desktop.json

nohup python src/endless_os_desktop.py > console.log 2>&1 &
