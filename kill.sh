ps -ef | grep endless_os_desktop | grep -v grep | awk '{print $2}' | xargs sudo kill -9
