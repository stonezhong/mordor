import os
import json
import yaml

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

    @property
    def pid_dir(self):
        return os.path.join(self.env_home, "pids", self.app_name)

    def get_json_config(self, filename):
        full_path = os.path.join(
            self.env_home, "configs", self.app_name, filename
        )
        with open(full_path, "r") as f:
            return json.load(f)

    def get_yaml_config(self, filename):
        full_path = os.path.join(
            self.env_home, "configs", self.app_name, filename
        )
        with open(full_path, "r") as f:
            return yaml.safe_load(f)

    def get_config(self, filename):
        if filename.endswith(".json"):
            return self.get_json_config(filename)
        if filename.endswith(".yaml"):
            return self.get_yaml_config(filename)
        assert False, "Only json or yaml are supported"

