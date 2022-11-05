from typing import Dict, List
import subprocess
import os
import glob
import tempfile

from .app_manifest import AppManifest
from .tools import get_config


class AppConfig:
    """Represent configuration for a given deployment
    """

    deployment_name: str  # the name of the deployment
    app_config: dict

    def __init__(self, deployment_name: str, app_config: dict):
        self.app_config = app_config
        self.deployment_name = deployment_name

        self.manifest = None
        for manifest_filename in [
            self.path("manifest.yaml"),
            self.path("manifest.json"),
        ]:
            if os.path.isfile(manifest_filename):
                self.manifest = AppManifest(get_config(manifest_filename))
                break
        if self.manifest is None:
            raise Exception("Missing manifest file")

    @property
    def name(self) -> str:
        return self.app_config.get("name", self.deployment_name)

    @property
    def stage(self) -> str:
        return self.app_config.get("stage", "")

    @property
    def home_dir(self) -> str:
        return self.app_config["home_dir"]

    @property
    def requirements(self) -> str:
        return self.app_config.get('requirements', 'requirements.txt')

    @property
    def use_python3(self) -> bool:
        return self.app_config.get("use_python3", True)

    @property
    def config(self) -> Dict[str, str]:
        # config files need to copied over
        return self.app_config.get("config", {})

    @property
    def deploy_to(self) -> List[str]:
        return self.app_config["deploy_to"]

    def path(self, *args) -> str:
        return os.path.join(self.home_dir, *args)

    @property
    def archive_filename(self) -> str:
        return "{}-{}.tar.gz".format(self.name, self.manifest.version)

    @property
    def venv_name(self) -> str:
        return "{}-{}".format(self.name, self.manifest.version)

    def create_archive(self) -> str:
        temp_dir = tempfile.mkdtemp()
        exclude_opts = []
        for exclude_dir in self.manifest.exclude_dirs:
            exclude_opts.extend(["--exclude", exclude_dir])

        args = ['tar'] + exclude_opts + [
            '-czf',
            os.path.join(temp_dir, self.archive_filename),
            "-C",
            self.home_dir
        ]
        files_to_add = glob.glob("{}/*".format(self.home_dir))
        files_to_add = [item[len(self.home_dir) + 1:] for item in files_to_add]
        args.extend(files_to_add)
        subprocess.check_call(args)
        return os.path.join(temp_dir, self.archive_filename)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "stage": self.stage,
            "home_dir": self.home_dir,
            "deploy_to": self.deploy_to,
            "manifest": self.manifest.to_json()
        }
