import os
from urlparse import urlparse
import re

class NameFormatUtil():
    def format(self, url):
        return self._url_to_name(url)
    
    def _format_host(self, host):
        host = host.replace('www.', '')
        for tld in self._tld_list():
            host = host.replace(tld, '')
        host = ' '.join(host.split('.')[::-1])
        # Re-combine the modified host
        return self._replace_special_characters_with_spaces(host)
    
    def _format_path(self, path):
        # If there's no http* then the whole URL ends up in 'path'...
        path = path.replace('www.', '')
        
        # removes leading and trailing /
        if path.endswith('/'):
            path = path[:-1]
        
        if path.startswith('/'):
            path = path[1:]
        
        path = path.split('/')
        
        if path != '':
            path = os.path.splitext(path[0])[0]
            
        return self._replace_special_characters_with_spaces(path)

    def _url_to_name(self, url):
        # Python's url parsing requires a protocol at the start, so add one
        # so that the library doesnt get confused.
        if not url.startswith("http"):
            url = 'http://'+ url
        url = urlparse(url)
        
        host = self._format_host(url.netloc)
        path = self._format_path(url.path)
             
        words = ' '.join([host, path])
        
        words = words.split()
        words = (s[0].upper() + s[1:] for s in words)
        
        return ' '.join(words)
    
    def _replace_special_characters_with_spaces(self, name):
        return re.sub('[^a-zA-Z0-9]', ' ', name)
    
    def _tld_list(self):
        return('.com','.edu','.gov','.int','.mil','.net','.org','.br','.ly','.se','co','uk')    