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
import base64
import shutil

class HostConfig(object):
    def __init__(self, host_name, host_config):
        self.host_config = host_config
        self.name = host_name

    @property
    def env_home(self):
        return self.host_config["env_home"]

    @property
    def ssh_host(self):
        return self.host_config["ssh_host"]

    @property
    def virtualenv(self):
        return self.host_config["virtualenv"]

    @property
    def python3(self):
        return self.host_config.get("python3")

    @property
    def ssh_key_filename(self):
        v = self.host_config.get("ssh_key_filename")
        if not v:
            return v
        return os.path.expanduser(v)

    @property
    def ssh_username(self):
        return self.host_config.get("ssh_username")

    def path(self, *args):
        return os.path.join(self.env_home, *args)

    def execute_batch(self, lines):
        with tempfile.NamedTemporaryFile(delete=True) as f:
            for line in lines:
                f.write(f"{line}\n".encode("utf-8"))
            f.write(f"exit\n".encode("utf-8"))
            f.seek(0)

            if self.ssh_key_filename:
                new_args = [
                    "ssh",
                    "-i",
                    self.ssh_key_filename,
                    "-q",
                    "{}@{}".format(self.ssh_username, self.ssh_host)
                ]
            else:
                new_args = ["ssh", "-q", self.ssh_host]
            subprocess.call(new_args, stdin=f)


    def execute(self, *args):
        if self.ssh_key_filename:
            new_args = [
                "ssh",
                "-i",
                self.ssh_key_filename,
                "-t",
                "-q",
                "{}@{}".format(self.ssh_username, self.ssh_host)
            ]
        else:
            new_args = ["ssh", "-q", "-t", self.ssh_host]
        new_args.extend(args)
        subprocess.call(new_args)

    # execute, wait for finish and get the output
    def execute2(self, *args):
        if self.ssh_key_filename:
            new_args = [
                "ssh",
                "-i",
                self.ssh_key_filename,
                "{}@{}".format(self.ssh_username, self.ssh_host)
            ]
        else:
            new_args = ["ssh", self.ssh_host]
        new_args.extend(args)
        p = subprocess.Popen(new_args, stdout=subprocess.PIPE)
        (output, err) = p.communicate()
        p_status = p.wait()
        return (output, err)

    def upload_batch(self, local_path, remote_path):
        if self.ssh_key_filename:
            new_args = [
                "scp", "-r", "-q", "-i", self.ssh_key_filename,
                local_path,
                "{}@{}:{}".format(
                    self.ssh_username,
                    self.ssh_host, remote_path
                )
            ]
        else:
            new_args = [
                "scp", "-r", "-q",
                local_path,
                "{}:{}".format(self.ssh_host, remote_path)
            ]

        subprocess.call(new_args)

    def upload(self, local_path, remote_path):
        if self.ssh_key_filename:
            new_args = [
                "scp", "-q", "-i", self.ssh_key_filename,
                local_path,
                "{}@{}:{}".format(
                    self.ssh_username,
                    self.ssh_host, remote_path
                )
            ]
        else:
            new_args = [
                "scp", "-q",
                local_path,
                "{}:{}".format(self.ssh_host, remote_path)
            ]

        subprocess.call(new_args)


class AppConfig(object):
    def __init__(self, deployment_name, app_config):
        self.app_config = app_config
        self.deployment_name = deployment_name
        self.manifest = AppManifest(get_json(self.path("manifest.json")))

    @property
    def stage(self):
        return self.app_config.get("stage")

    @property
    def name(self):
        return self.app_config.get("name", self.deployment_name)

    @property
    def home_dir(self):
        return self.app_config["home_dir"]

    @property
    def use_python3(self):
        return self.app_config.get("use_python3", False)

    @property
    def config(self):
        # config files need to copied over
        return self.app_config.get("config", {})

    @property
    def deploy_to(self):
        return self.app_config["deploy_to"]

    def path(self, *args):
        return os.path.join(self.home_dir, *args)

    @property
    def archive_filename(self):
        return "{}-{}.tar.gz".format(self.name, self.manifest.version)

    @property
    def venv_name(self):
        return "{}-{}".format(self.name, self.manifest.version)


    def create_archive(self):
        temp_dir = tempfile.mkdtemp()
        exclude_opts = [ ]
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
        subprocess.call(args)
        return os.path.join(temp_dir, self.archive_filename)


class Config(object):
    def __init__(self, config, config_dir):
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

    def get_host(self, host_name):
        return self.host_dict[host_name]

    def get_app(self, app_name, stage=None):
        return self.app_dict[app_name].get(stage)


def get_json(path):
    with open(os.path.expanduser(path), "r") as f:
        return json.load(f)


class AppManifest(object):
    def __init__(self, manifest):
        self.manifest = manifest

    @property
    def version(self):
        return self.manifest["version"]

    @property
    def exclude_dirs(self):
        return self.manifest.get("exclude_dirs", [])


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
        "run_dispatcher.sh",
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
def stage_app(base_dir, config, app_name, update_venv, config_only, stage=None, host_name=None):
    app = config.get_app(app_name, stage=stage)
    if app is None:
        print("Application {} with stage {} does not exist".format(app_name, stage))
        exit(1)

    # archive the entire app and send it to host
    # tar -czf /tmp/a.tar.gz -C $PWD *
    if not config_only:
        archive_filename = app.create_archive()
    else:
        archive_filename = None

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
        stage_app_on_host(base_dir, config, app, host, archive_filename, update_venv, config_only, stage=stage)


def stage_app_on_host(base_dir, config, app, host, archive_filename, update_venv, config_only, stage=None):
    print("stage application \"{}\" for stage \"{}\" on host \"{}\"".format(
        app.name, app.stage, host.name
    ))
    # allow user to have different configs for different stages
    config_base_dir = os.path.join(config.config_dir, "configs", app.name)
    app_config_dirs = []
    if stage is not None:
        # if stage is specified, we will look if there is a config for the stage
        staged_config_base_dir = os.path.join(config_base_dir, stage)
        if os.path.isdir(staged_config_base_dir):
            app_config_dirs.append(staged_config_base_dir)
    app_config_dirs.append(config_base_dir)

    def find_config_filename(name):
        for prefix in app_config_dirs:
            full_name = os.path.join(prefix, name)
            if os.path.isfile(full_name):
                return full_name
        raise Exception("Config file {} does not exist!".format(name))

    # creating local staging area for upload file via scp
    temp_dir = tempfile.mkdtemp()
    local_stage_dir = os.path.join(temp_dir, app.name)
    os.makedirs(local_stage_dir)
    if not config_only:
        shutil.copyfile(archive_filename, os.path.join(local_stage_dir, app.archive_filename))
    for (filename, deploy_type) in app.config.items():
        if deploy_type == "copy":
            shutil.copyfile(
                find_config_filename(filename),
                os.path.join(local_stage_dir, filename)
            )
            continue
        if deploy_type == "convert":
            with open(find_config_filename(filename), "r") as f:
                content = f.read()
            config_dir = os.path.join(host.env_home, "configs", app.name)
            content = content.format(
                config_dir=config_dir,
                env_home=host.env_home,
                app_name=app.name
            )
            with open(os.path.join(local_stage_dir, filename), "w") as sf:
                sf.write(content.encode("utf-8"))
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
        # create directorys
        lines.extend([
            f"mkdir -p {host.path('apps', app.name)}",
            f"mkdir -p {host.path('apps', app.name, app.manifest.version)}",
            f"rm -rf {host.path('apps', app.name, app.manifest.version, '*')}",
            f"mkdir -p {host.path('logs', app.name)}",
            f"mkdir -p {host.path('configs', app.name)}",
            f"mkdir -p {host.path('data', app.name)}",
            # remove and re-create the sym link point to the current version of the app
            f"rm -f {host.path('apps', app.name, 'current')}",
            f"ln -s {host.path('apps', app.name, app.manifest.version)} {host.path('apps', app.name, 'current')}",
            # extract app archive
            f"tar -xzf {host.path('temp', app.name, app.archive_filename)} -C {host.path('apps', app.name, app.manifest.version)}",
        ])
    # move config file from temp dir
    for filename in app.config.keys():
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
            lines.append(f"{host.path('bin', 'install_packages.sh')} {host.env_home} {app.name} {app.manifest.version}")
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
    print("")

    return


def run_app(base_dir, config, app_name, stage = None, host_name = None, cmd = ""):
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
        run_app_on_host(base_dir, config, app, host, cmd)


def run_app_on_host(base_dir, config, app, host, cmd):
    print("running application: \"{}\" on host \"{}\"".format(app.name, host.name))
    print("            command: \"{}\"".format(cmd))

    cmd_to_send = base64.b64encode(cmd.encode('utf-8')).decode('utf-8')


    host.execute(
        host.path("bin", "run_dispatcher.sh"),
        host.env_home,
        app.name,
        cmd_to_send
    )
    return


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


def main():
    parser = argparse.ArgumentParser(
        description='Mordor deployment tool for python'
    )
    parser.add_argument(
        "-a", "--action", type=str, required=True, help="Specify action",
        choices=['init-host', 'stage', 'run', 'kill', 'status']
    )
    parser.add_argument(
        "-o", "--host-name", type=str, required=False, help="destination host"
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
        default=os.environ.get("MORDOR_CONFIG_DIR", "~/.mordor")
    )
    args = parser.parse_args()

    # validate options
    if args.update_venv and args.config_only:
        raise Exception("You cannot specify --update-venv and --config-only both")

    base_dir = os.path.abspath(os.path.dirname(__file__))

    # get the config file
    config_dir = os.path.expanduser(args.config_dir)
    config = Config(
        get_json(os.path.join(args.config_dir, 'config.json')),
        config_dir
    )

    if args.action == "init-host":
        if not args.host_name:
            print("--host-name must be specified")
            return
        init_host(base_dir, config, args.host_name)
        return

    if args.action == "stage":
        if not args.app_name:
            print("--app-name must be specified")
            return
        stage_app(
            base_dir, config, args.app_name, args.update_venv, args.config_only,
            stage = args.stage,
            host_name = args.host_name
        )
        return

    if args.action == "run":
        run_app(
            base_dir, config, args.app_name,
            stage = args.stage,
            host_name = args.host_name,
            cmd = args.cmd
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
