#!/bin/bash +e

checkout_dir=/home/endlessm/checkout

REPOS=( \
      'eos-desktop' \
      'eos-common' \
     #'eos-config' \
     #'eos-browser' \
      )

sudo apt-get install git -y

sudo mkdir -p ${checkout_dir}

echo -n "Enter branch, type [dev] if you are unsure, then press [ENTER]"
read branch

pushd ${checkout_dir}

  for repo in ${REPOS[@]}
  do
    sudo git clone http://github.com/endlessm/${repo}.git
    pushd ${repo}
      sudo git checkout ${branch}
      ./build.sh
    popd
  done

popd

sudo chown -R endlessm:endlessm ${checkout_dir}
