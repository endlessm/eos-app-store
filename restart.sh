#!/bin/bash

desktop_dir=/home/endlessm/checkout/eos-desktop

if [ "$1" -a "clean" == "$1" ]; then
    echo "cleaning desktop json and installed applications..."
    rm ~/.endlessm/desktop.json
    rm ~/.endlessm/installed_applications.json
fi

pushd ${desktop_dir}

  export DISPLAY=:0

  ps -ef | grep endless_os_desktop | grep -v grep | awk '{print $2}' | xargs kill -9
  nohup python src/endless_os_desktop.py > console.log 2>&1 &

popd
