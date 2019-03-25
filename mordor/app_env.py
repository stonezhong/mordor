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
            parser = argparse.ArgumentParser(add_help=False)
            parser.add_argument("--app_name", type=str, required=False, help="Application name")
            parser.add_argument("--env_home", type=str, required=False, help="Environment home")
            args, _ = parser.parse_known_args()

            env_home = args.env_home or os.environ["env_home"]
            app_name = args.app_name or os.environ["app_name"]

            if not env_home or not app_name:
                raise Exception("env_home or app_name not set")

            cls.theEnv = cls(env_home, app_name)
        return cls.theEnv


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
