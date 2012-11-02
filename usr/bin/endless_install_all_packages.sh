#!/bin/bash -e

/usr/bin/endless-pre-install.sh

export DEBIAN_FRONTEND=noninteractive
dpkg -i --force-confnew $ENDLESS_DOWNLOAD_DIRECTORY/*

#FIXME: add auto fix here - kam & mct

/usr/bin/endless-post-install.sh

rm -f /usr/bin/endless-pre-install.sh
rm -f /usr/bin/endless-post-install.sh