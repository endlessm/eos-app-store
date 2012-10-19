ps -ef | grep endless_os_desktop | awk '{print $2}' |xargs sudo kill -9
