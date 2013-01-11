#!/bin/bash 

sudo apt-get install -y python-setuptools
sudo easy_install lettuce ldtp


pushd $(dirname $0) &> /dev/null
   export PYTHONPATH=src:features/support

   lettuce
popd &> /dev/null
