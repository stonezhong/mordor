import argparse
import os
import json

class AppEnv(object):
    def __init__(self, env_home, app_name):
        self.env_home = env_home
        self.app_name = app_name

    theEnv = None

    @classmethod
    def get(cls):
        if cls.theEnv is None:
            parser = argparse.ArgumentParser()
            parser.add_argument("--app_name", type=str, required=True, help="Application name")
            parser.add_argument("--env_home", type=str, required=True, help="Environment home")
            args, _ = parser.parse_known_args()

            cls.theEnv = cls(args.env_home, args.app_name)
        return cls.theEnv


    @property
    def log_dir(self):
        return os.path(self.env_home, "logs", self.app_name)

    @property
    def data_dir(self):
        return os.path(self.env_home, "data", self.app_name)

    @property
    def config_dir(self):
        return os.path(self.env_home, "configs", self.app_name)

    def get_json_config(self, filename):
        with os.path(self.env_home, "configs", self.app_name, filename) as f:
            return json.load(f)
