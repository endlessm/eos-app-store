#!/bin/bash

sudo apt-get install git -y

mkdir -p ~/checkout

git clone http://github.com/endlessm/eos-desktop.git

cd ~/checkout/eos-desktop

git status

git checkout -b issues/439
