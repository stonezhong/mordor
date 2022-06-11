import argparse
import os
import json

class AppEnv(object):
    def __init__(self, app_name):
        self.env_home = os.environ["ENV_HOME"]
        self.app_name = app_name

    @property
    def log_dir(self):
        return os.path.join(self.env_home, "logs", self.app_name)

    @property
    def data_dir(self):
        return os.path.join(self.env_home, "data", self.app_name)

    @property
    def config_dir(self):
        return os.path.join(self.env_home, "configs", self.app_name)

    def get_json_config(self, filename):
        full_path = os.path.join(
            self.env_home, "configs", self.app_name, filename
        )
        with open(full_path, "r") as f:
            return json.load(f)
