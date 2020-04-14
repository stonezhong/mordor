import os
import tempfile
import glob
import subprocess
import json

from .cache import cached

class Application(object):
    def __init__(self, mordor, config):
        self.mordor = mordor
        self.config = config
        self._cache = {}


    @property
    def id(self):
        return self.config['id']


    @property
    @cached('home_dir')
    def home_dir(self):
        v = self.config['home_dir']
        v = os.path.expanduser(v)
        v = os.path.expandvars(v)
        return v
    

    @property
    def support_python2(self):
        return self.config.get("support_python2", False)


    @property
    def support_python3(self):
        return self.config.get("support_python3", False)


    @property
    @cached('manifest')
    def manifest(self):
        manifest_filename = os.path.join(self.home_dir, "manifest.json")
        with open(manifest_filename, "rt") as f:
            return json.load(f)


    def create_archive(self):
        # create archive file from the application
        tmp_file = tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False)
        args = [
            'tar',
            '-czf',
            tmp_file.name,
            "-C",
            self.home_dir
        ]
        files_to_add = glob.glob("{}/*".format(self.home_dir))
        files_to_add = [item[len(self.home_dir) + 1:] for item in files_to_add]
        args.extend(files_to_add)
        subprocess.call(args)
        return tmp_file.name


    def build(self, host, args):
        remote_root_dir = host.mordor_info['root_dir']
        remote_app_dir = os.path.join(remote_root_dir, "applications", self.id)
        remote_app_archive_filename = os.path.join(remote_app_dir, self.manifest['version'] + '.tar.gz')
        remote_app_version_dir      = os.path.join(remote_app_dir, self.manifest['version'])

        local_app_archive_filename = self.create_archive()
        host.execute("mkdir", "-p", remote_app_version_dir)

        host.execute('rm', '-f', remote_app_archive_filename)
        host.upload(
            local_app_archive_filename, 
            remote_app_archive_filename
        )
        host.execute('rm', '-rf', os.path.join(remote_app_version_dir, 'src'))
        host.execute("mkdir", os.path.join(remote_app_version_dir, 'src'))
        host.execute(
            "tar", 
            "-xzf", 
            remote_app_archive_filename, 
            "-C", os.path.join(remote_app_version_dir, 'src')
        )
        host.execute('rm', remote_app_archive_filename)

        if args.update_venv == 'T':
            # build virtualenv
            if self.support_python2:
                if host.python2 is None:
                    raise Exception("The host {} does not support python2!".format(host.id))
                remote_venv_path = os.path.join(remote_app_version_dir, 'venv_p2')
                host.execute("rm", "-rf",     remote_venv_path)
                host.execute("mkdir", "-p",   remote_venv_path)
                host.execute(host.virtualenv, remote_venv_path)
                remote_python = os.path.join(remote_venv_path, 'bin', 'python')
                host.execute(remote_python, "-m", "pip", "install", "pip", "setuptools", "--upgrade")
                host.execute(
                    remote_python, "-m", "pip", "install", "-r", 
                    os.path.join(remote_app_version_dir, "src", "requirements.txt")
                )
            else:
                print("Bypass python2 setup since this application does not support python2")
            
            if self.support_python3:
                if host.python3 is None:
                    raise Exception("The host {} does not support python3!".format(host.id))
                remote_venv_path = os.path.join(remote_app_version_dir, 'venv_p3')
                host.execute("rm", "-rf",     remote_venv_path)
                host.execute("mkdir", "-p",   remote_venv_path)
                host.execute(host.python3, "-m", "venv", remote_venv_path)
                remote_python = os.path.join(remote_venv_path, 'bin', 'python')
                host.execute(remote_python, "-m", "pip", "install", "pip", "setuptools", "--upgrade")
                host.execute(
                    remote_python, "-m", "pip", "install", "-r", 
                    os.path.join(remote_app_version_dir, "src", "requirements.txt")
                )
            else:
                print("Bypass python3 setup since this application does not support python3")
