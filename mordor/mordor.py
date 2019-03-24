#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import argparse 
import subprocess
import os
import json
import tempfile
import glob

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
            
    def execute(self, *args):
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

    def upload(self, local_path, remote_path):
        if self.ssh_key_filename:        
            new_args = [
                "scp", "-i", self.ssh_key_filename,
                local_path,
                "{}@{}:{}".format(
                    self.ssh_username,
                    self.ssh_host, remote_path
                )
            ]
        else:
            new_args = [
                "scp",
                local_path,
                "{}:{}".format(self.ssh_host, remote_path)
            ]

        subprocess.call(new_args)
    
class AppConfig(object):
    def __init__(self, name, app_config):
        self.app_config = app_config
        self.name = name
        self.manifest = AppManifest(get_json(self.path("manifest.json")))
    
    @property
    def home_dir(self):
        return self.app_config["home_dir"]
    
    @property
    def cmd(self):
        return self.app_config.get("cmd", "run.sh")

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
        args = [
            'tar', 
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
    def __init__(self, config):
        self.config = config
        self.host_dict = {}
        for (host_name, host_config) in self.config["hosts"].items():
            self.host_dict[host_name] = HostConfig(host_name, host_config)
        self.app_dict = {}
        for (app_name, app_config) in self.config["applications"].items():
            self.app_dict[app_name] = AppConfig(app_name, app_config)
    
    def get_host(self, host_name):
        return self.host_dict[host_name]
    
    def get_app(self, app_name):
        return self.app_dict[app_name]

def get_json(path):
    with open(os.path.expanduser(path), "r") as f:
        return json.load(f)

class AppManifest(object):
    def __init__(self, manifest):
        self.manifest = manifest
    
    @property
    def version(self):
        return self.manifest["version"]

# Initialize a given server so it can run python code
def init_host(base_dir, config, host_name):
    host = config.get_host(host_name)
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
    ]
    for cmd in cmds:
        host.upload(
            os.path.join(base_dir, "bin", cmd),
            host.path("bin", cmd)
        )
        host.execute("chmod", "+x", host.path("bin", cmd))


# stage an python application on the target host
def stage_app(base_dir, config, app_name, update_venv):
    app = config.get_app(app_name)

    # archive the entire app and send it to host
    # tar -czf /tmp/a.tar.gz -C $PWD *
    archive_filename = app.create_archive()
    for host_name in app.deploy_to:
        host = config.get_host(host_name)
        stage_app_on_host(base_dir, config, app, host, archive_filename, update_venv)
    
def stage_app_on_host(base_dir, config, app, host, archive_filename, update_venv):
    print("stage application \"{}\" on host \"{}\"".format(app.name, host.name))
    # copy app archive to remote host
    host.upload(archive_filename, host.path("temp", app.archive_filename))

    # create directorys
    host.execute("mkdir", "-p" , host.path("apps", app.name))
    host.execute("mkdir", "-p" , host.path("apps", app.name, app.manifest.version))
    host.execute("rm",    "-rf", host.path("apps", app.name, app.manifest.version, "*"))
    host.execute("mkdir", "-p" , host.path("logs", app.name))
    host.execute("mkdir", "-p" , host.path("configs", app.name))
    host.execute("mkdir", "-p" , host.path("data", app.name))

    # remove and re-create the sym link point to the current version of the app
    host.execute("rm",    "-f",  host.path("apps", app.name, "current"))
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

    for (filename, deploy_type) in app.config.items():
        if deploy_type == "copy":
            host.upload(
                os.path.join(
                    os.path.expanduser("~/.mordor/configs"), 
                    app.name,
                    filename
                ),
                host.path("configs", app.name, filename),
            )
            continue
        if deploy_type == "convert":
            with open(
                os.path.join(os.path.expanduser("~/.mordor/configs"), app.name, filename),
                "r"
            ) as f:
                content = f.read()
            config_dir = os.path.join(host.env_home, "configs", app.name)
            content = content.format(
                config_dir = config_dir,
                env_home = host.env_home,
                app_name = app.name
            )
            tf = tempfile.NamedTemporaryFile(delete = False)
            tf.file.write(content.encode("utf-8"))
            tf.file.close()
            host.upload(tf.name, host.path("configs", app.name, filename))
            continue
    return

def run_app(base_dir, config, app_name):
    app = config.get_app(app_name)
    print("running application: \"{}\", cmd: \"{}\"".format(app.name, app.cmd))
    for host_name in app.deploy_to:
        host = config.get_host(host_name)
        run_app_on_host(base_dir, config, app, host)

def run_app_on_host(base_dir, config, app, host):
    print("    {}".format(host.name))
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


def kill_app(base_dir, config, app_name):
    app = config.get_app(app_name)
    print("killing application \"{}\"".format(app.name))
    for host_name in app.deploy_to:
        host = config.get_host(host_name)
        kill_app_on_host(base_dir, config, app, host)

def kill_app_on_host(base_dir, config, app, host):
    print("    {}".format(host.name))
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
        "-a", "--action", type=str, required=True, help="action"
    )
    parser.add_argument(
        "-o", "--host_name", type=str, required=False, help="destination host"
    )
    parser.add_argument(
        "-p", "--app_name", type=str, required=False, help="application name"
    )
    parser.add_argument(
        "--update_venv",  
        type=str, 
        required=False, 
        default="T", 
        help="Should I update virtual env?"
    )
    args = parser.parse_args()

    base_dir = os.path.abspath(os.path.dirname(__file__))

    # get the config file
    config = Config(get_json("~/.mordor/config.json"))

    if args.action == "init_host":
        if not args.host_name:
            print("--host_name must be specified")
            return
        init_host(base_dir, config, args.host_name)
        return
    
    if args.action =="stage":
        if not args.app_name:
            print("--app_name must be specified")
            return
        stage_app(base_dir, config, args.app_name, args.update_venv == 'T')
        return
    
    if args.action == "run":
        run_app(base_dir, config, args.app_name)
        return

    if args.action == "kill":
        kill_app(base_dir, config, args.app_name)
        return

    if args.action == "status":
        get_app_status(base_dir, config, args.app_name)
        return

    raise Exception("unrecognized action")

if __name__ == '__main__':
    main()
