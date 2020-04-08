class Compartment(object):
    def __init__(self, mordor, config):
        self.mordor = mordor
        self.config = config

    @property
    def id(self):
        return self.config['id']
    
    @property
    def host(self):
        host_id = self.config['host']
        host = self.mordor.hosts[host_id]
        return host

