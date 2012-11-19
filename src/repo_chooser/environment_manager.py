from startup.auto_updates import endpoint_provider

class EnvironmentManager(object):
    PROD_PASS = "production"
    DEMO_PASS = "demonstration"
    DEV_PASS = "development"
    APT_TESTING_PASS = "apttesting"

    PROD_NAME = ""
    DEMO_NAME = "DEMO "
    DEV_NAME = "DEV "
    APT_TESTING_NAME = "APT TESTING "

    PROD_URL = "http://apt.endlessdevelopment.com/updates"
    DEMO_URL = "http://apt.endlessdevelopment.com/demo"
    DEV_URL = "http://em-vm-build"
    APT_TESTING_URL = "http://apt.endlessdevelopment.com/apt_testing"
    
    REPOS = [ 
        (PROD_NAME, PROD_PASS, PROD_URL),
        (DEMO_NAME, DEMO_PASS, DEMO_URL),
        (DEV_NAME, DEV_PASS, DEV_URL),
        (APT_TESTING_NAME, APT_TESTING_PASS, APT_TESTING_URL),
        ]

    def get_current_repo(self):
        url = endpoint_provider.get_endless_url()

        for repo in self.REPOS:
            if repo[2] == url:
                return repo[0]

        endpoint_provider.set_endless_url(self.PROD_URL)
        return self.get_current_repo()


    def set_current_repo(self, password):
        for repo in self.REPOS:
            if repo[1] == password:
                endpoint_provider.set_endless_url(repo[2])
                break
        else: 
            endpoint_provider.set_endless_url(self.PROD_URL)

