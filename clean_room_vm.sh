#!/bin/bash

sudo apt-get install python-alsaaudio

sudo rm -rf /etc/endlessm
sudo rm -rf /usr/share/endlessm
sudo ln -s $PWD /etc/endlessm
sudo ln -s $PWD /usr/share/endlessm

