import os

class Configuration(object):
    def __init__(self, mordor, config):
        self.mordor = mordor
        self.config = config
    
    @property
    def id(self):
        return self.config['id']
    
    @property
    def location(self):
        v = self.config['location']
        v = os.path.expanduser(v)
        v = os.path.expandvars(v)
        return v
    
    @property
    def type(self):
        return self.config['type']
    
    @property
    def name(self):
        if 'name' in self.config:
            return self.config['name']
        return os.path.basename(self.config['location'])


