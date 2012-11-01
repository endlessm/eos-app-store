#!/bin/bash -e

/usr/bin/endless-pre-install.sh

dpkg -i $ENDLESS_DOWNLOAD_DIRECTORY/*

/usr/bin/endless-post-install.sh

rm -f /usr/bin/endless-pre-install.sh
rm -f /usr/bin/endless-post-install.sh