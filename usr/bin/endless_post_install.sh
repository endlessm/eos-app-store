#!/bin/bash

SCRIPT=/var/lib/endless/packages/endless_post_install.sh

if [ -e $SCRIPT ]
then
    . $SCRIPT
fi
