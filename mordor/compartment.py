from .cache import cached

class Compartment(object):
    def __init__(self, mordor, config):
        self.mordor = mordor
        self.config = config
        self._cache = {}

    @property
    def id(self):
        return self.config['id']
    
    @property
    @cached('hosts')
    def hosts(self):
        ret = []
        for host_id in self.config['hosts']:
            host = self.mordor.hosts[host_id]
            ret.append(host)
        return ret
