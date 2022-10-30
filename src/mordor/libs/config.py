from typing import Dict, Optional

from collections import defaultdict
from .host_config import HostConfig
from .app_config import AppConfig


class Config:
    config_dir: str  # the location of the config directory
    config: dict     # the overall config
    host_dict: Dict[str, HostConfig]  # for all hosts
    app_dict: Dict[str, Dict[str, AppConfig]]    # for all applications, first level key is application name,
    # 2nd level key is stage name

    def __init__(self, config: dict, config_dir: str):
        self.config_dir = config_dir
        self.config = config
        self.host_dict = {}
        for (host_name, host_config) in self.config["hosts"].items():
            self.host_dict[host_name] = HostConfig(host_name, host_config)
        self.app_dict = defaultdict(dict)  # key is deployment_name

        deployments = self.config.get("deployments") or self.config.get("applications")
        if deployments is None:
            raise Exception("Missing deployments section")

        for (deployment_name, app_config) in deployments.items():
            app = AppConfig(deployment_name, app_config)
            if app.stage in self.app_dict[app.name]:
                raise Exception("Duplicate: application = {}, stage = {}".format(app.name, app.stage))
            else:
                self.app_dict[app.name][app.stage] = app

    def get_host(self, host_name: str) -> Optional[HostConfig]:
        return self.host_dict.get(host_name)

    def get_app(self, app_name: str, stage: str) -> AppConfig:
        if app_name not in self.app_dict:
            return None
        return self.app_dict[app_name].get(stage)

