#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from typing import Optional, List
import argparse
import os
import sys
import tempfile
import shutil
import base64
from enum import Enum
import json

from jinja2 import Template

from .libs import Config, get_config, AppConfig, HostConfig

class ConfigDeployType(Enum):
    COPY        = "copy"
    CONVERT     = "convert"
    TEMPLATE    = "template"

def init_hosts(base_dir: str, config: Config, host_names: List[str]) -> None:
    host_dict = {}
    for host_name in host_names:
        host = config.get_host(host_name)
        if host is None:
            print(f"Host {host_name} does not exist.")
            sys.exit(1)
        else:
            host_dict[host_name] = host

    for host_name in host_names:
        init_host(base_dir, config, host_dict[host_name])


def init_host(base_dir: str, config: Config, host: HostConfig) -> None:
    """ Initialize a host for mordor

    :param base_dir:
    :param config:
    :param host:
    :return: Nothing
    """

    print(f"Initialize mordor for host {host.name} ...")
    for dir_name in [
        host.env_home,
        host.path("bin"),
        host.path("apps"),
        host.path("venvs"),
        host.path("pids"),
        host.path("logs"),
        host.path("configs"),
        host.path("data"),
        host.path("temp"),
    ]:
        host.execute("mkdir", "-p", dir_name)

    cmds = [
        "install_packages.sh",
        "run_dispatcher.sh",
        "init_host.sh",
        "host_tools.txt",
    ]
    for cmd in cmds:
        host.upload(
            os.path.join(base_dir, "bin", cmd),
            host.path("bin", cmd)
        )
        if cmd.endswith(".sh"):
            host.execute("chmod", "+x", host.path("bin", cmd))

    host.execute(host.path("bin", "init_host.sh"), host.env_home)
    print(f"Done!")


def stage_app(
    config: Config,
    app_name: str,
    update_venv: bool,
    config_only: bool,
    stage: str = '',
    host_names: Optional[List[str]] = None
) -> None:
    """ Stage an application on the fleet for a stage

    :param base_dir: name of the directory contains mordor.py
    :param config: overall config
    :param app_name: application name
    :param update_venv: create virtual environment or not
    :param config_only: update config only or not
    :param stage: application stage, e.g., "beta", "prod", etc.
    :param host_names: if specified, we only stage to this list of hosts, otherwise, we stage to all hosts for the stage
    :return: Nothing
    """
    app = config.get_app(app_name, stage)
    if app is None:
        print(f"Application {app_name} with stage {stage} does not exist.")
        sys.exit(1)
    if not app.use_python3:
        print(f"Application {app_name} with stage {stage} does not support python3.")
        sys.exit(1)

    # archive the entire app and send it to host
    # tar -czf /tmp/a.tar.gz -C $PWD *
    if not config_only:
        archive_filename = app.create_archive()
    else:
        archive_filename = None

    if host_names is not None:
        deploy_to = host_names
    else:
        deploy_to = app.deploy_to

    # do a check first
    for host_name in deploy_to:
        host = config.get_host(host_name)
        if host is None:
            print(f"Host {host_name} does not exist.")
            sys.exit(1)

    for host_name in deploy_to:
        host = config.get_host(host_name)
        stage_app_on_host(config, app, host, archive_filename, update_venv, config_only, stage=stage)


def stage_app_on_host(
    config: Config,
    app: AppConfig,
    host: HostConfig,
    archive_filename: str,
    update_venv: bool,
    config_only: bool,
    stage: str = ''
) -> None:
    """ Stage an application on target host

    :param config: overall config
    :param app: application config
    :param host: host config
    :param archive_filename: the application archive filename
    :param update_venv: create virtual environment or not
    :param config_only: update config only or not
    :param stage: application stage, e.g., "beta", "prod", etc.
    :return: Nothing
    """
    print(f"Stage application {app.name} for stage {app.stage} on host {host.name}.")
    # allow user to have different configs for different stages
    config_base_dir = os.path.join(config.config_dir, "configs", app.name)
    app_config_dirs = []

    def add_dir_to_config_dirs(dir_name: str) -> None:
        if os.path.isdir(dir_name) and dir_name not in app_config_dirs:
            app_config_dirs.append(dir_name)

    add_dir_to_config_dirs(os.path.join(config_base_dir, stage, host.name))
    add_dir_to_config_dirs(os.path.join(config_base_dir, stage))
    add_dir_to_config_dirs(config_base_dir)

    def find_config_filename(name: str) -> str:
        for prefix in app_config_dirs:
            full_name = os.path.join(prefix, name)
            if os.path.isfile(full_name):
                return full_name
        print(f"Config file {name} does not exist.")
        sys.exit(1)

    # creating local staging area for upload file via scp
    temp_dir = tempfile.mkdtemp()
    local_stage_dir = os.path.join(temp_dir, app.name)
    os.makedirs(local_stage_dir)
    if not config_only:
        shutil.copyfile(archive_filename, os.path.join(local_stage_dir, app.archive_filename))
    # generate metadata.json
    metadata_filename = os.path.join(local_stage_dir, "_deployment.json")
    with open(metadata_filename, "wt") as f:
        json.dump(
            {
                "host": host.to_json(),
                "app": app.to_json(),
            },
            f,
            indent=4
        )
    for (filename, deploy_type) in app.config.items():
        if deploy_type == ConfigDeployType.COPY.value:
            shutil.copyfile(
                find_config_filename(filename),
                os.path.join(local_stage_dir, filename)
            )
            continue
        if deploy_type == ConfigDeployType.CONVERT.value:
            with open(find_config_filename(filename), "r") as f:
                content = f.read()
            config_dir = os.path.join(host.env_home, "configs", app.name)
            content = content.format(
                config_dir=config_dir,
                env_home=host.env_home,
                app_name=app.name
            )
            with open(os.path.join(local_stage_dir, filename), "w") as sf:
                sf.write(content)
            continue
        if deploy_type == ConfigDeployType.TEMPLATE.value:
            with open(find_config_filename(filename), "rt") as f:
                template = Template(f.read())
                context = {
                    "host_name": host.name,
                    "config_dir": os.path.join(host.env_home, "configs", app.name),
                    "log_dir": os.path.join(host.env_home, "logs", app.name),
                    "data_dir": os.path.join(host.env_home, "data", app.name),
                    "pid_dir": os.path.join(host.env_home, "pids", app.name),
                    "env_home": host.env_home,
                    "app_name": app.name
                }
            with open(os.path.join(local_stage_dir, filename), "wt") as sf:
                sf.write(template.render(context))
            continue

    if not config_only:
        print("    Upload application and configuration ... ", end="", flush=True)
    else:
        print("    Upload configuration ... ", end="", flush=True)
    host.upload_batch(local_stage_dir, host.path("temp"))
    print("Done!")

    # copy app archive to remote host
    lines = []
    if not config_only:
        # create directories
        lines.extend([
            f"mkdir -p {host.path('apps', app.name)}",
            f"mkdir -p {host.path('apps', app.name, app.manifest.version)}",
            f"rm -rf {host.path('apps', app.name, app.manifest.version, '*')}",
            f"mkdir -p {host.path('logs', app.name)}",
            f"mkdir -p {host.path('configs', app.name)}",
            f"mkdir -p {host.path('data', app.name)}",
            f"mkdir -p {host.path('pids', app.name)}",
            # remove and re-create the sym link point to the current version of the app
            f"rm -f {host.path('apps', app.name, 'current')}",
            f"ln -s {host.path('apps', app.name, app.manifest.version)} {host.path('apps', app.name, 'current')}",
            # extract app archive
            f"tar -xzf {host.path('temp', app.name, app.archive_filename)} -C {host.path('apps', app.name, app.manifest.version)}",
        ])
    # move config file from temp dir
    for filename in list(app.config.keys()) + ['_deployment.json']:
        lines.append(f"mv {host.path('temp', app.name, filename)} {host.path('configs', app.name, filename)}")
    if not config_only:
        # finally, let's remove the archive_filename and staging area in temp
        lines.append(f"rm {host.path('temp', app.name, app.archive_filename)}")
    lines.append(f"rmdir {host.path('temp', app.name)}")

    if not config_only:
        # recreate venv since dependencies may have changed
        if update_venv:
            lines.append(f"rm -rf {host.path('venvs', app.venv_name)}")
            if app.use_python3:
                lines.append(f"{host.python3} -m venv {host.path('venvs', app.venv_name)}")
            else:
                lines.append(f"{host.virtualenv} {host.path('venvs', app.venv_name)}")
            lines.append(
                f"{host.path('bin', 'install_packages.sh')} {host.env_home} {app.name} {app.manifest.version} {app.requirements}")
            lines.append(f"rm -f {host.path('venvs', app.name)}")
            # create a symlink
            lines.append(f"ln -s {host.path('venvs', app.venv_name)} {host.path('venvs', app.name)}")
            print("    Update application, configuration and virtual environment ... ", end="", flush=True)
        else:
            print("    Update application and configuration ... ", end="", flush=True)
    else:
        print("    Update configuration ... ", end="", flush=True)

    host.execute_batch(lines)
    print("Done!")

    if app.manifest.on_stage is not None:
        run_app_on_host(app, host, app.manifest.on_stage, prefix="    ")
    print("Done!")
    print("")


def run_app(
    config: Config,
    app_name: str,
    stage:str = '',
    host_names: Optional[List[str]] = None,
    cmd:str = ""
) -> None:
    """Run an application on the fleet for a stage

    :param config: overall config
    :param app_name: application name
    :param stage: application stage, e.g., "beta", "prod", etc.
    :param host_names: if specified, we only stage to this list of hosts, otherwise, we stage to all hosts for the stage
    :param cmd: the command to run
    :return: Nothing
    """
    app = config.get_app(app_name, stage)
    if app is None:
        print(f"Application {app_name} with stage {stage} does not exist.")
        sys.exit(1)
    if not app.use_python3:
        print(f"Application {app_name} with stage {stage} does not support python3.")
        sys.exit(1)

    if host_names is not None:
        run_on = [host_names]
    else:
        run_on = app.deploy_to

    # do a check first
    for host_name in run_on:
        host = config.get_host(host_name)
        if host is None:
            print(f"Host {host_name} does not exist.")
            sys.exit(1)

    for host_name in run_on:
        host = config.get_host(host_name)
        run_app_on_host(app, host, cmd)


def run_app_on_host(
    app: AppConfig,
    host: HostConfig,
    cmd: str,
    prefix:str = ""
):
    """ Run an application on target host

    :param app: application config
    :param host: host config
    :param cmd: command to run
    :return: Nothing
    """
    print(f"{prefix}Running application {app.name} on host {host.name}, cmd: \"{cmd}\".")

    cmd_to_send = base64.b64encode(cmd.encode('utf-8')).decode('utf-8')

    host.execute(
        host.path("bin", "run_dispatcher.sh"),
        host.env_home,
        app.name,
        cmd_to_send
    )

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Mordor deployment tool for python.'
    )
    parser.add_argument(
        "action", type=str, help="Specify action",
        choices=['init-host', 'stage', 'run'],
        nargs=1
    )
    parser.add_argument(
        "-o", "--host-names", type=str, default=None, required=False, nargs='+',
        help="destination hosts"
    )
    parser.add_argument(
        "-p", "--app-name", type=str, required=False, help="application name"
    )
    parser.add_argument(
        "-s", "--stage", type=str, required=False, help="stage"
    )
    parser.add_argument(
        "-cmd", "--cmd", type=str, required=False, help="command to run",
        default=""
    )
    parser.add_argument(
        "--update-venv",
        action="store_true",
        help="Specify if you want to update virtualenv",
    )
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Specify if you want to stage configuration only",
    )
    parser.add_argument(
        "-c", "--config-dir", type=str, required=False, help="Configuration directory",
        default=os.environ.get("MORDOR_CONFIG_DIR", os.path.expanduser("~/.mordor"))
    )
    args = parser.parse_args()

    action = args.action[0]

    # validate options
    if args.update_venv and args.config_only:
        print("You cannot specify both --update-venv and --config-only")
        sys.exit(1)

    base_dir = os.path.abspath(os.path.dirname(__file__))

    # get the config file
    config_dir = os.path.expanduser(args.config_dir)
    for filename in [
        os.path.join(args.config_dir, 'config.yaml'),
        os.path.join(args.config_dir, 'config.json'),
        None
    ]:
        if filename is not None and os.path.isfile(filename):
            break
    if filename is None:
        print(f"Missing config file in directory {args.config_dir}")
        sys.exit(1)

    config = Config(get_config(filename), config_dir)

    if action == "init-host":
        if not args.host_names:
            print("--host-names must be specified.")
            sys.exit(1)
        init_hosts(base_dir, config, args.host_names)
        return

    if action == "stage":
        if not args.app_name:
            print("--app-name must be specified.")
            sys.exit(1)
        stage_app(
            config, args.app_name, args.update_venv, args.config_only,
            stage=args.stage,
            host_names=args.host_names
        )
        return

    if action == "run":
        run_app(
            config, args.app_name,
            stage = args.stage,
            host_names = args.host_names,
            cmd = args.cmd
        )
        return

if __name__ == '__main__':
    main()
