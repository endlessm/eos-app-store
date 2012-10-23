#!/bin/bash +e

checkout_dir=/home/endlessm/checkout
build_script=build.sh
app_list=/etc/endlessm/application.list
desktop_file=/home/endlessm/.endlessm/desktop.json

if [ -d ${checkout_dir} ]; then
  sudo rm -rf ${checkout_dir}
fi

REPOS=( \
      'eos-desktop' \
      'eos-common' \
     #'eos-config' \
     #'eos-browser' \
      )

sudo apt-get install git -y

sudo mkdir -p ${checkout_dir}

echo -n "Enter branch, type [dev] if you are unsure, then press [ENTER]:\n"
read branch

pushd ${checkout_dir}

  for repo in ${REPOS[@]}
  do
    sudo git clone http://github.com/endlessm/${repo}.git
    pushd ${repo}
      sudo git checkout ${branch}
      if [ -f ${build_script} ]; then
        ./${build_script}
      fi
    popd
  done

popd

sudo chown -R endlessm:endlessm ${checkout_dir}

replacement=$',{"key":"terminal","icon":"/usr/share/icons/gnome/48x48/apps/gnome-terminal.png","name":"Terminal"},{"key":"terminal","icon":"/usr/share/icons/gnome/48x48/apps/gnome-terminal.png","name":"QA","params":["--command","/home/endlessm/checkout/eos-desktop/restart-launcher.sh"]}]'

if ! grep -q terminal ${app_list}
then
  echo "updating ${app_list}..."
  sudo sed -i'.bak' -e's/}$/  ,"terminal":"gnome-terminal.desktop"\n}/' ${app_list}
fi  

if ! grep -q terminal ${desktop_file}
then
  echo "updating ${desktop_file}"
  sudo sed -i'.bak' -e"s|\]$|${replacement}|" ${desktop_file}
fi  
