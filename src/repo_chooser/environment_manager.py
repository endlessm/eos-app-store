from repo_def import RepoDef

class EnvironmentManager(object):
    DEFAULT_KEY = "prod"
    DEMO_KEY = "demo"
    DEV_KEY = "dev"
    APT_TESTING_KEY = "apttesting"
       
    PROD_PASS = "production"
    DEMO_PASS = "demonstration"
    DEV_PASS = "development"
    APT_TESTING_PASS = "apttesting"
    
    REPOS = { 
                PROD_PASS : DEFAULT_KEY,
                DEMO_PASS : DEMO_KEY,
                DEV_PASS : DEV_KEY,
                APT_TESTING_PASS : APT_TESTING_KEY,
        }

    DATA = {
                DEFAULT_KEY : RepoDef("", "http://apt.endlessdevelopment.com/updates"),
                DEMO_KEY : RepoDef("DEMO ", "http://apt.endlessdevelopment.com/demo"),
                DEV_KEY : RepoDef("DEV ", "http://em-vm-build"),
                APT_TESTING_KEY : RepoDef("APT TESTING ", "http://apt.endlessdevelopment.com/apt_testing")
            }
    
    def find_repo(self, password):
        if password and password in self.REPOS:
            key = self.REPOS[password]
            return self.DATA[key]
        return self.DATA[self.DEFAULT_KEY]           

