#!/bin/bash

eos_desktop_dir=/home/endlessm/checkout/eos-desktop

pushd ${eos_desktop_dir}
  nohup ./restart.sh > console-start.log 2>&1 &
popd

sleep 1
