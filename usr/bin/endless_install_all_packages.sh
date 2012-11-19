#!/bin/bash -e

if [ $# -ne 1 ]
then
    echo "Wrong number of arguments"
    exit 1
fi

if [ ! -d $1 ]
then
    echo "$1 is not a directory"
    exit 1
fi

pushd $1 &> /dev/null
    PACKAGE_DIRECTORY=$(pwd)
popd &> /dev/null


if [ $(ls $PACKAGE_DIRECTORY | egrep deb$ | wc -l) -eq 0 ]
then
    echo "No debian packages were found in $PACKAGE_DIRECTORY"
    exit 1
fi

set +e
dpkg -iGE --force-confnew ${PACKAGE_DIRECTORY}/*.deb &>> /tmp/endless_auto_updates.log
if [[ $? -ne 0 ]]
then
    rm /var/lib/dpkg/updates/*
    dpkg -a --configure
    apt-get -f install
fi
set -e

