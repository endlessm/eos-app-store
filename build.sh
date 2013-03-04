#!/bin/bash -e

# Install dependencies
sudo apt-get install -y devscripts debhelper python-xlib python-alsaaudio hal
sudo easy_install nose

pushd `dirname $0`
  script_dir=`pwd`
  apps_dir=~/apps
  pyinstaller_dir="${apps_dir}/pyinstaller-2.0"

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
      unzip ${script_dir}/tools/pyinstaller*.zip -d ${apps_dir}
    popd 
  fi

  pushd ../eos-build &> /dev/null
  INSTALL_DIR=$(pwd)
  export GNUPGHOME=${INSTALL_DIR}/gnupg
  popd &> /dev/null

  # Build package
  debuild -k4EB55A92 -b
  
  # Move package to this directory and clean up
  mv ../endlessos-base-desktop*.deb .
  mv ../endlessos-base-desktop*.changes .
  rm -f ../*.build

    if [[ $(dpkg -c *.deb | egrep "py$") ]]
    then
        echo "There are python source files in the debian package!"
        exit 1
    else
        echo "There are no python source files in the debian package"
    fi
    
popd
