import urllib
import urllib2
import socket

class WebConnection():
    AUTHORIZED_REALMS = [ "apt.endlessm.com",
                          "apt.endlessdevelopment.com" ]
    
    def get(self, url, username=None, password=None):
        if username: 
            self._setup_authentication(url, username, password)
        
        try:
            return urllib2.urlopen(url).read()
        except Exception as e:
            self._handle_error(e, url, username)

    def _handle_error(self, e, url, is_authenticated=False):
        message = ""
        if isinstance(e, ValueError):
            message = e.message
        elif isinstance(e, urllib2.HTTPError):
            message = e.msg

        raise Exception("Could not access url ({url}){using_auth}: {error}".format(url=url, error=message, using_auth=" using authentication" if is_authenticated else ""))
        
    def send(self, url, data, username=None, password=None):
        if username:
            self._setup_authentication(url, username, password)
        
        params = urllib.urlencode(data)
        headers = {"Content-type":"application/x-www-form-urlencoded", "Accept":"application/json"}
        request = urllib2.Request(url, params, headers)

        try:
            connection = urllib2.urlopen(request)
            connection.close()
        except Exception as e:
            self._handle_error(e, url, username)

    def _setup_authentication(self, server, username, password):
        socket.setdefaulttimeout(15)
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        
        for realm in self.AUTHORIZED_REALMS:
            passman.add_password(None, realm, username, password)
        passman.add_password(None, server, username, password)
            
        authhandler = urllib2.HTTPBasicAuthHandler(passman)

        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
