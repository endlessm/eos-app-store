#!/bin/bash -e

sudo wget $ENDLESS_ENDPOINT/install/endless-pre-install.sh /usr/bin/endless-pre-install.sh 
sudo wget $ENDLESS_ENDPOINT/install/endless-post-install.sh /usr/bin/endless-post-install.sh

sudo apt-get -y -d -o Dir::Cache::Archives=$ENDLESS_DOWNLOAD_DIRECTORY install endless*
