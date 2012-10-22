#!/bin/bash

checkout_dir=/home/endlessm/checkout

sudo apt-get install git -y

sudo mkdir -p ${checkout_dir}

pushd ${checkout_dir}

sudo git clone http://github.com/endlessm/eos-desktop.git

pushd eos-desktop
git status

sudo git checkout issues/439

popd

echo "done with git.."

popd

echo "done with script.."

sudo chown -R endlessm:endlessm ${checkout_dir}
