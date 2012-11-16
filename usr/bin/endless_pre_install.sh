#!/bin/bash

SCRIPT=/var/lib/endless/packages/endless_pre_install.sh

if [ -e $SCRIPT ]
then
    . $SCRIPT
fi
