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
    def home_dir(self):
        return self.host_config["home_dir"]
        
    @property
    def virtualenv(self):
        return self.host_config["virtualenv"]

    def path(self, *args):
        return os.path.join(self.home_dir, *args)
            
    def execute(self, *args):
        remote_hostname = self.host_config["ssh_host"]        
        new_args = ["ssh", remote_hostname]
        new_args.extend(args)
        subprocess.call(new_args)
    
    def upload(self, local_path, remote_path):
        remote_hostname = self.host_config["ssh_host"]        
        subprocess.call([
            "scp",
            local_path,
            "{}:{}".format(remote_hostname, remote_path)
        ])
    
class AppConfig(object):
    def __init__(self, name, app_config):
        self.app_config = app_config
        self.name = name
        self.manifest = AppManifest(get_json(self.path("manifest.json")))
    
    @property
    def home_dir(self):
        return self.app_config["home_dir"]
    
    @property
    def config(self):
        # config files need to copied over
        return self.app_config["config"]
    
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
        host.home_dir,
        host.path("bin"),
        host.path("apps"),
        host.path("venvs"),
        host.path("pids"),
        host.path("logs"),
        host.path("configs"),
        host.path("temp"),
    ]:
        host.execute("mkdir", "-vp", dir)

    host.upload(
        os.path.join(base_dir, "bin", "install_packages.sh"),
        host.path("bin", "install_packages.sh")
    )
    host.upload(
        os.path.join(base_dir, "bin", "run_app.sh"),
        host.path("bin", "run_app.sh")
    )

    host.execute("chmod", "+x", host.path("bin", "install_packages.sh"))
    host.execute("chmod", "+x", host.path("bin", "run_app.sh"))

# stage an python application on the target host
def stage_app(base_dir, config, app_name):
    app = config.get_app(app_name)

    # archive the entire app and send it to host
    # tar -czf /tmp/a.tar.gz -C $PWD *
    archive_filename = app.create_archive()
    for host_name in app.deploy_to:
        host = config.get_host(host_name)
        stage_app_on_host(base_dir, config, app, host, archive_filename)
    
def stage_app_on_host(base_dir, config, app, host, archive_filename):
    # copy app archive to remote host
    host.upload(archive_filename, host.path("temp", app.archive_filename))

    # create directorys
    host.execute("mkdir", "-p" , host.path("apps", app.name))
    host.execute("mkdir", "-p" , host.path("apps", app.name, app.manifest.version))
    host.execute("rm",    "-rf", host.path("apps", app.name, app.manifest.version, "*"))
    host.execute("mkdir", "-p" , host.path("logs", app.name))
    host.execute("mkdir", "-p" , host.path("configs", app.name))

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
    host.execute("rm", "-rf", host.path("venvs", app.venv_name))
    host.execute(host.virtualenv, host.path("venvs", app.venv_name))
    host.execute(
        host.path("bin", "install_packages.sh"), 
        host.home_dir,
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
            content = content.format(
                home_dir = host.home_dir,
                app_name = app.name
            )
            tf = tempfile.NamedTemporaryFile(delete = False)
            tf.file.write(content)
            tf.file.close()
            host.upload(tf.name, host.path("configs", app.name, filename))
            continue
    return



def run_app(base_dir, config, app_name):
    app = config.get_app(app_name)
    for host_name in app.deploy_to:
        host = config.get_host(host_name)
        run_app_on_host(base_dir, config, app, host)

def run_app_on_host(base_dir, config, app, host):
    print("running application \"{}\" on host \"{}\"".format(app.name, host.name))
    host.execute(
        host.path("bin", "run_app.sh"),
        host.home_dir,
        app.name
    )

def main():
    parser = argparse.ArgumentParser(description='Mordor deployment tool for python')
    parser.add_argument("-a", "--action",    type=str, required=True, help="action")
    parser.add_argument("-o", "--host_name", type=str, required=False, help="destination host")
    parser.add_argument("-p", "--app_name",  type=str, required=False, help="application name")
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
        stage_app(base_dir, config, args.app_name)
        return
    
    if args.action == "run":
        run_app(base_dir, config, args.app_name)
        return
    
    raise Exception("unrecognized action")

if __name__ == '__main__':
    main()
