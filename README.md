Endless OS - Desktop Widget
===========================

Dev environment
---------------
  - Install Ubuntu 12.04 LTS 32-bit
  - Python 2.7 (installed by default on 12.04)
  - Update Ubuntu packages
    ``sudo apt-get update``
    ``sudo apt-get upgrade -y``
    ``sudo apt-get install -y aptitude``
  - Install Debian package builders
    ``sudo apt-get install -y devscripts debhelper``
  - Install Gtk helper libraries for attaching images
    ``sudo apt-get install -y libgtk-3-dev``
  - Install Nosetest testing suite
    ``sudo apt-get install -y python-setuptools``
    ``sudo easy_install nose``
    ``sudo easy_install mock``
  - Install git
    ``sudo apt-get install -y git``
  - Download the endless client package
    - Navigate to ``http://apt.endlessm.com/updates/install``
    - user=endlessos
    - pass=install
    - Download the latest version
  - Install the endless client package (use the appropriate version number)
    ``sudo dpkg -i endless-installer_1.0-6_i386.deb``
    - Hit OK to restart the OS when prompted
  - Python development IDE or VIM
    - We use Aptana Studio with PyDev plugin
    - You can get Aptana from ``http://aptana.com/``


Downloading the Dev Package
---------------------------
  - The source code will be provided by Endless Mobile
  - Unpack the ZIP file
    ``unzip endless-os-desktop-widget.zip``
    ``cd endless-os-desktop-widget/``


Running the application
-----------------------
  - From command line
    ``python src/endless_os_desktop.py &``
  - From Aptana
    - Right click ``endless_os_desktop.py`` in src folder and select Run As->Python Run


Running tests
-------------
  - From command line
    ``nosetests``
  - From Aptana
    - Right click test folder and select Run As->Python unit-test


Git workflow for most stories
-----------------------------
  - Fetch origin
    ``git fetch origin``
  - Checkout dev branch
    ``git checkout dev``
  - Make sure it's up to date 
    ``git reset --hard origin/dev``
  - Checkout feature branch (usually ``xxxxx_friendly_name`` where xxxxx is the task number)
    ``git checkout -b 10123_some_feature``
  - Write code and save all
    - Do magic here
  - Commit
    ``git add .``
    ``git commit -m "Some commit message -Your Name"``
  - Fetch origin
    ``git fetch origin``
  - Checkout dev branch
    ``git checkout dev``
  - Make sure it's up to date 
    ``git reset --hard origin/dev``
  - Checkout feature branch
    ``git checkout 10123_some_feature``
  - Merge dev branch into the feature branch without fast-forwarding
    ``git merge --no-ff dev``
  - Checkout dev branch
    ``git checkout dev``
  - Merge feature branch into the dev branch
    ``git merge --no-ff 10123_some_feature``
  - Push changes on dev to origin
    ``git push origin dev``


