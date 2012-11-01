import apt_pkg
from urlparse import urlparse

def get_current_apt_endpoint():
    apt_pkg.init_config()
    apt_pkg.init_system()
    acquire = apt_pkg.Acquire()
    slist = apt_pkg.SourceList()
    slist.read_main_list()
    slist.get_indexes(acquire, True)

    url = "em-vm-build/repository"
    for item in acquire.items:
        if "endless" in item.desc_uri:
            parsed_url = urlparse(item.desc_uri)
            url = parsed_url.hostname + "/" + parsed_url.path.split("/")[1]
            break

    return "http://" + url
    
if __name__ == '__main__':
    print get_current_apt_endpoint()


