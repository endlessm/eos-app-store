#!/bin/bash -e

# Install dependencies
DEPENDENCIES="devscripts debhelper python-xlib"
set +e 
  dpkg -s $DEPENDENCIES &> /dev/null
  has_dependencies=$?
set -e

if [[ $has_dependencies -ne 0 ]]; then
  sudo apt-get install -y $DEPENDENCIES
fi
sudo easy_install nose

pushd `dirname $0`
  script_dir=`pwd`
  apps_dir=~/apps

  # Clean up old deb packages
  set +e
    rm -rf ./*.deb
    rm -rf ./*.changes
  set -e
  
  pushd ../eos-build &> /dev/null
  INSTALL_DIR=$(pwd)
  export GNUPGHOME=${INSTALL_DIR}/gnupg
  popd &> /dev/null

  mkdir -p mo/es_GT
  mkdir -p mo/pt_BR
  msgfmt -v po/es_GT.po -o mo/es_GT/eos_app_store.mo
  msgfmt -v po/pt_BR.po -o mo/pt_BR/eos_app_store.mo

  # Build package
  export DEB_PACKAGE_NAME=$(head -n 1 debian/changelog | awk '{print $1}') 
  debuild -k4EB55A92 -b
  
  # Move package to this directory and clean up
  mv ../eos-app-store*.deb .
  mv ../eos-app-store*.changes .
  rm -f ../*.build

    if [[ $(dpkg -c *.deb | egrep "py$") ]]
    then
        echo "There are python source files in the debian package!"
        exit 1
    else
        echo "There are no python source files in the debian package"
    fi
    
popd
