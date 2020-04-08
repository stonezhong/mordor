import os
import json

class AppEnv(object):
    def __init__(self):
        self.base_dir = os.path.dirname(os.getenv('PWD'))
    
    @property
    def data_dir(self):
        return os.path.join(self.base_dir, 'data')

    @property
    def config_dir(self):
        return os.path.join(self.base_dir, 'config')

    @property
    def log_dir(self):
        return os.path.join(self.base_dir, 'log')

    def get_json_config(self, name):
        filename = os.path.join(self.base_dir, 'config', name)
        with open(filename, 'rt') as f:
            return json.load(f)

