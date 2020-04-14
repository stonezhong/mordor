import os
from .cache import cached

class AnonymousConfiguration(object):
    def __init__(self, mordor, config):
        self.mordor = mordor
        self.config = config
        self._cache = {}
   
    @property
    @cached('location')
    def location(self):
        v = self.config['location']
        v = os.path.expanduser(v)
        v = os.path.expandvars(v)
        return v
    
    @property
    def type(self):
        return self.config['type']
    
    @property
    @cached('name')
    def name(self):
        if 'name' in self.config:
            return self.config['name']
        return os.path.basename(self.config['location'])


class Configuration(AnonymousConfiguration):
    def __init__(self, mordor, config):
        super(Configuration, self).__init__(mordor, config)
    
    @property
    def id(self):
        return self.config['id']
    
