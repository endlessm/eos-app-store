#!/bin/bash -e

wget $ENDLESS_ENDPOINT/install/endless-pre-install.sh /usr/bin/endless-pre-install.sh 
wget $ENDLESS_ENDPOINT/install/endless-post-install.sh /usr/bin/endless-post-install.sh

apt-get -y -d -o Dir::Cache::Archives=$ENDLESS_DOWNLOAD_DIRECTORY install endless*
