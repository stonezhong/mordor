#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import argparse
import subprocess
import os
import json
import tempfile
import glob
from collections import defaultdict
from jinja2 import Template


class Config(object):
    def __init__(self, config):
        self.config = config
        self.host_dict = {}
        for (host_name, host_config) in self.config["hosts"].items():
            self.host_dict[host_name] = HostConfig(host_name, host_config)
        self.app_dict = defaultdict(dict)  # key is deployment_name
        for (deployment_name, app_config) in self.config["applications"].items():
            app = AppConfig(deployment_name, app_config)
            if app.stage in self.app_dict[app.name]:
                raise Exception("Duplicate: application = {}, stage = {}".format(app.name, app.stage))
            else:
                self.app_dict[app.name][app.stage] = app

    def get_host(self, host_name):
        return self.host_dict[host_name]

    def get_app(self, app_name, stage=None):
        return self.app_dict[app_name].get(stage)




class AppManifest(object):
    def __init__(self, manifest):
        self.manifest = manifest

    @property
    def version(self):
        return self.manifest["version"]


# Initialize a given server so it can run python code
def init_host(base_dir, config, host_name):
    host = config.get_host(host_name)
    if host is None:
        print("Host {} does not exist".format(host_name))
        exit(1)

    for dir in [
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
        host.execute("mkdir", "-vp", dir)

    cmds = [
        "install_packages.sh",
        "run_app.sh",
        "run_app_py.sh",
        "get_app_status.sh",
        "kill_app.sh",
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

# stage an python application on the target host
def stage_app(base_dir, config, app_name, update_venv, stage=None, host_name=None):
    app = config.get_app(app_name, stage=stage)
    if app is None:
        print("Application {} with stage {} does not exist".format(app_name, stage))
        exit(1)

    # archive the entire app and send it to host
    # tar -czf /tmp/a.tar.gz -C $PWD *
    archive_filename = app.create_archive()
    if host_name is not None:
        deploy_to = [host_name]
    else:
        deploy_to = app.deploy_to

    # do a check first
    for host_name in deploy_to:
        host = config.get_host(host_name)
        if host is None:
            print("Host {} does not exist".format(host_name))
            exit(1)

    for host_name in deploy_to:
        host = config.get_host(host_name)
        stage_app_on_host(base_dir, config, app, host, archive_filename, update_venv, stage=stage)


def stage_app_on_host(base_dir, config, app, host, archive_filename, update_venv, stage=None):
    print("stage application \"{}\" for stage \"{}\" on host \"{}\"".format(
        app.name, app.stage, host.name
    ))
    # copy app archive to remote host
    host.upload(archive_filename, host.path("temp", app.archive_filename))

    # create directorys
    host.execute("mkdir", "-p", host.path("apps", app.name))
    host.execute("mkdir", "-p", host.path("apps", app.name, app.manifest.version))
    host.execute("rm", "-rf", host.path("apps", app.name, app.manifest.version, "*"))
    host.execute("mkdir", "-p", host.path("logs", app.name))
    host.execute("mkdir", "-p", host.path("configs", app.name))
    host.execute("mkdir", "-p", host.path("data", app.name))

    # remove and re-create the sym link point to the current version of the app
    host.execute("rm", "-f", host.path("apps", app.name, "current"))
    host.execute(
        "ln",
        "-s",
        host.path("apps", app.name, app.manifest.version),
        host.path("apps", app.name, "current")
    )

    # extract app archive
    host.execute(
        'tar',
        '-xzf',
        host.path("temp", app.archive_filename),
        "-C",
        host.path("apps", app.name, app.manifest.version)
    )

    # recreate venv since dependencies may have changed
    if update_venv:
        host.execute("rm", "-rf", host.path("venvs", app.venv_name))
        if app.use_python3:
            host.execute(host.virtualenv, "-p", host.python3, host.path("venvs", app.venv_name))
        else:
            host.execute(host.virtualenv, host.path("venvs", app.venv_name))
        host.execute(
            host.path("bin", "install_packages.sh"),
            host.env_home,
            app.name,
            app.manifest.version
        )
        # create a symlink
        host.execute("rm", "-f", host.path("venvs", app.name))
        host.execute("ln", "-s",
                     host.path("venvs", app.venv_name),
                     host.path("venvs", app.name)
                     )

    # allow user to have different configs for different stages
    config_base_dir = os.path.join(os.path.expanduser("~/.mordor/configs"), app.name)
    if stage is not None:
        staged_config_base_dir = os.path.join(config_base_dir, stage)
        if os.path.isdir(staged_config_base_dir):
            config_base_dir = staged_config_base_dir

    for (filename, deploy_type) in app.config.items():
        if deploy_type == "copy":
            host.upload(
                os.path.join(config_base_dir, filename),
                host.path("configs", app.name, filename),
            )
            continue
        if deploy_type == "convert":
            with open(
                    os.path.join(config_base_dir, filename),
                    "rt"
            ) as f:
                content = f.read()
            config_dir = os.path.join(host.env_home, "configs", app.name)
            content = content.format(
                config_dir=config_dir,
                env_home=host.env_home,
                app_name=app.name
            )
            tf = tempfile.NamedTemporaryFile(delete=False)
            tf.file.write(content.encode("utf-8"))
            tf.file.close()
            host.upload(tf.name, host.path("configs", app.name, filename))
            continue
        if deploy_type == 'template':
            with open(
                    os.path.join(config_base_dir, filename),
                    "rt"
            ) as f:
                content = f.read()
            config_dir = os.path.join(host.env_home, "configs", app.name)
            t = Template(content)
            content = t.render(
                config_dir=config_dir,
                env_home=host.env_home,
                app_name=app.name
            )
            tf = tempfile.NamedTemporaryFile(delete=False)
            tf.file.write(content.encode("utf-8"))
            tf.file.close()
            host.upload(tf.name, host.path("configs", app.name, filename))
            continue

    return


def run_app(base_dir, config, app_name, stage = None, host_name = None):
    app = config.get_app(app_name, stage=stage)
    if app is None:
        print("Application {} with stage {} does not exist".format(app_name, stage))
        exit(1)

    if host_name is not None:
        run_on = [host_name]
    else:
        run_on = app.deploy_to

    # do a check first
    for host_name in run_on:
        host = config.get_host(host_name)
        if host is None:
            print("Host {} does not exist".format(host_name))
            exit(1)

    for host_name in run_on:
        host = config.get_host(host_name)
        run_app_on_host(base_dir, config, app, host)


def run_app_on_host(base_dir, config, app, host):
    print("running application: \"{}\", cmd: \"{}\", on \"{}\"".format(app.name, app.cmd, host.name))

    if app.cmd.endswith(".sh"):
        host.execute(
            host.path("bin", "run_app.sh"),
            host.env_home,
            app.name,
            app.cmd
        )
        return
    if app.cmd.endswith(".py"):
        host.execute(
            host.path("bin", "run_app_py.sh"),
            host.env_home,
            app.name,
            app.cmd
        )
        return
    print("    Invalid launcher")


def kill_app(base_dir, config, app_name, stage = None, host_name = None):
    app = config.get_app(app_name, stage=stage)
    if app is None:
        print("Application {} with stage {} does not exist".format(app_name, stage))
        exit(1)

    if host_name is not None:
        kill_on = [host_name]
    else:
        kill_on = app.deploy_to

    # do a check first
    for host_name in kill_on:
        host = config.get_host(host_name)
        if host is None:
            print("Host {} does not exist".format(host_name))
            exit(1)

    for host_name in kill_on:
        host = config.get_host(host_name)
        kill_app_on_host(base_dir, config, app, host)


def kill_app_on_host(base_dir, config, app, host):
    print("killing application \"{}\" for stage \"\" on \"\"".format(
        app.name, app.stage, host.name
    ))
    host.execute(
        host.path("bin", "kill_app.sh"),
        host.env_home,
        app.name
    )


def get_app_status(base_dir, config, app_name):
    app = config.get_app(app_name)
    print("status of application \"{}\"".format(app.name))
    for host_name in app.deploy_to:
        host = config.get_host(host_name)
        get_app_status_on_host(base_dir, config, app, host)


def get_app_status_on_host(base_dir, config, app, host):
    output, err = host.execute2(
        host.path("bin", "get_app_status.sh"),
        host.env_home,
        app.name
    )
    print('    {}: {}'.format(host.name, output.decode('utf-8')))


def get_global_config():
    return Config(get_json("~/.mordor/config.json"))

def main():
    parser = argparse.ArgumentParser(
        description='Mordor deployment tool for python'
    )
    parser.add_argument(
        "-a", "--action", type=str, required=True, help="action. Could be init-target, stage, run, kill or status"
    )
    parser.add_argument(
        "-o", "--target-name", type=str, required=False, help="destination target"
    )
    parser.add_argument(
        "-p", "--app-name", type=str, required=False, help="application name"
    )
    parser.add_argument(
        "-s", "--stage", type=str, required=False, help="stage"
    )
    parser.add_argument(
        "--update-venv",
        type=str,
        required=False,
        default="T",
        help="Specify T if you want to update virtualenv, F if not. Default is T"
    )
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.dirname(__file__))

    # get the config file
    config = get_global_config()

    if args.action == "init-target":
        if not args.target_name:
            print("--target-name must be specified")
            return
        init_target(base_dir, config, args.target_name)
        return

    if args.action == "stage":
        if not args.app_name:
            print("--app-name must be specified")
            return
        stage_app(
            base_dir, config, args.app_name, args.update_venv == 'T', 
            stage = args.stage,
            host_name = args.host_name
        )
        return

    if args.action == "run":
        run_app(
            base_dir, config, args.app_name, 
            stage = args.stage, 
            host_name = args.host_name
        )
        return

    if args.action == "kill":
        kill_app(
            base_dir, config, args.app_name, 
            stage = args.stage, 
            host_name = args.host_name
        )
        return

    if args.action == "status":
        get_app_status(base_dir, config, args.app_name)
        return

    raise Exception("unrecognized action")


if __name__ == '__main__':
    main()