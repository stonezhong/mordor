import os
import json
import yaml
import glob
import shutil
import importlib
from copy import deepcopy
from typing import Optional
from jinja2 import Template
from .libs.tools import get_config
from .libs.app_manifest import AppManifest

class AppEnv:
    def __init__(self, app_name: str, version:Optional[str] = None, env_home:Optional[str] = None):
        self.env_home = os.environ["ENV_HOME"] if env_home is None else env_home
        self.app_name = app_name
        self._manifest = None

        if version is None:
            app_base_dir = os.path.join(self.env_home, "apps", self.app_name, "current")
            manifest_filenames = [
                os.path.join(app_base_dir, "manifest.yaml"),
                os.path.join(app_base_dir, "manifest.json"),
            ]
            app_manifest = None
            for manifest_filename in manifest_filenames:
                if os.path.isfile(manifest_filename):
                    app_manifest = AppManifest(get_config(manifest_filename))
                    break
            if app_manifest is None:
                raise Exception("Missing manifest")
            self.version = app_manifest.version
        else:
            self.version = version

    @property
    def app_dir(self) -> str:
        return os.path.join(self.env_home, "apps", self.app_name, self.version)

    @property
    def log_dir(self) -> str:
        return os.path.join(self.env_home, "logs", self.app_name)

    @property
    def data_dir(self) -> str:
        return os.path.join(self.env_home, "data", self.app_name)

    @property
    def config_dir(self) -> str:
        return os.path.join(self.env_home, "configs", self.app_name)

    @property
    def pid_dir(self) -> str:
        return os.path.join(self.env_home, "pids", self.app_name)

    @property
    def venv_dir(self) -> str:
        return os.path.join(self.env_home, "venvs", f"{self.app_name}-{self.version}")

    def get_json_config(self, filename: str):
        full_path = os.path.join(
            self.env_home, "configs", self.app_name, filename
        )
        with open(full_path, "r") as f:
            return json.load(f)

    def get_yaml_config(self, filename: str):
        full_path = os.path.join(
            self.env_home, "configs", self.app_name, filename
        )
        with open(full_path, "r") as f:
            return yaml.safe_load(f)

    def get_config(self, filename: str):
        if filename.endswith(".json"):
            return self.get_json_config(filename)
        if filename.endswith(".yaml"):
            return self.get_yaml_config(filename)
        assert False, "Only json or yaml are supported"

def deltree(p:str) -> None:
    """ Delete everything inside a directory

    :param p: directory location
    :return: Nothing
    """
    files = []
    files.extend(glob.glob(os.path.join(p, ".*"), recursive=False))
    files.extend(glob.glob(os.path.join(p, "*"), recursive=False))
    for file in files:
        if os.path.isfile(file):
            os.remove(file)
        elif os.path.isdir(file):
            shutil.rmtree(file)


def prepare_for_docker(app_name: str, context: dict = {}) -> None:
    app_env = AppEnv(app_name)
    _context = app_env.get_config("_deployment.json")
    _context.update(context)
    process_templates(app_name, "docker", _context)
    app_docker_dir = os.path.join(app_env.data_dir, "docker", "app")
    if os.path.isdir(app_docker_dir):
        shutil.rmtree(app_docker_dir)
    def to_ignore(dir_name, contents):
        if dir_name == app_env.app_dir:
            return ['docker']
        else:
            return []
    shutil.copytree(
        os.path.join(app_env.app_dir),
        app_docker_dir,
        symlinks=True,
        ignore=to_ignore
    )


def process_templates(app_name: str, template_dir: str, context: dict) -> None:
    """ Process template directory, result stored in data dir

    :param app_name: application name
    :param template_dir: the relative path name of the template directory, relative to the app home
    :param context: the context we need to bind to
    :return: Nothing
    """

    app_env = AppEnv(app_name)
    src_dir = os.path.join(app_env.app_dir)
    dst_dir = os.path.join(app_env.data_dir)

    dst_template_dir = os.path.join(dst_dir, template_dir)
    os.makedirs(dst_template_dir, exist_ok=True)
    deltree(dst_template_dir)

    process_templates_dir(src_dir, dst_dir, template_dir, context)

def process_templates_dir(src_base_dir:str, dst_base_dir:str, template_dir: str, context: dict):
    src_dir = os.path.join(src_base_dir, template_dir)
    dst_dir = os.path.join(dst_base_dir, template_dir)

    if os.path.isfile(os.path.join(src_dir, "context.py")):
        module = importlib.import_module(
            ".".join(list(os.path.split(template_dir))[1:] + ['context'])
        )
        get_context = getattr(module, 'get_context')
        local_context = get_context(deepcopy(context))
    else:
        local_context = context

    for file in os.listdir(src_dir):
        if file in ("context.py", "__pycache__"):
            continue
        src_filename = os.path.join(src_dir, file)

        if os.path.isfile(src_filename):
            if src_filename.endswith(".template"):
                with open(src_filename, "rt") as rf:
                    template = Template(rf.read())
                    dst_filename = os.path.join(dst_dir, file[:-9]) # remove .template
                    with open(dst_filename, "wt") as wf:
                        wf.write(template.render(local_context))
            else:
                dst_filename = os.path.join(dst_dir, file)
                shutil.copyfile(src_filename, dst_filename)
        elif os.path.isdir(src_filename):
            sub_template_dir = os.path.join(template_dir, file)
            os.makedirs(os.path.join(dst_base_dir, sub_template_dir), exist_ok=False)
            process_templates_dir(src_base_dir, dst_base_dir, sub_template_dir, local_context)
