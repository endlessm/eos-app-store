#!/bin/bash -e

# Install dependencies
sudo apt-get install -y devscripts debhelper
sudo easy_install nose

pushd `dirname $0`
  script_dir=`pwd`
  apps_dir=~/apps
  pyinstaller_dir="${apps_dir}/pyinstaller-1.5.1"

  # Clean up old deb packages
  set +e
    rm -rf ./*.deb
    rm -rf ./*.changes
  set -e
  
  if [[ ! -d ${pyinstaller_dir} ]]; then
    echo "No PyInstaller found in ${apps_dir}. Extracting packaged version"
    mkdir -p ${apps_dir}
    pushd ${apps_dir}
      echo "Extracting from ${script_dir}"
      tar -xjf ${script_dir}/tools/pyinstaller*.tar.bz2
    popd 
  fi

  if [[ ! -e ${pyinstaller_dir}/config.dat ]];then
    echo "No configuration found. Configuring PyInstaller"
    python ${pyinstaller_dir}/Configure.py
  fi
  
  echo "Converting glade files to .py files"
  pushd ui &> /dev/null
    ./convert.sh
  popd &> /dev/null

  pushd ../desktop* &> /dev/null
  INSTALL_DIR=$(pwd)
  export GNUPGHOME=${INSTALL_DIR}/gnupg
  popd &> /dev/null

  # Build package
  debuild -k4EB55A92 -b
  
  # Move package to this directory and clean up
  mv ../endless-os-desktop-widget*.deb .
  mv ../endless-os-desktop-widget*.changes .
  rm -f ../*.build
popd
