import subprocess
import tempfile
import os
import json
import uuid

from .cache import cached

class Host(object):
    def __init__(self, mordor, config):
        self.mordor = mordor
        self.config = config
        self._cache = {}
    
    @property
    def id(self):
        return self.config['id']

    @property
    def type(self):
        return self.config['type']
    
    @property
    def host(self):
        return self.config['host']

    @property
    def container(self):
        return self.config.get('container')
   
    @property
    def per_user(self):
        # mordor can be installed per system or per user
        # if this is True, then we are using mordor as current user
        # otherwise, we are using the system wide mordor
        return self.config.get('per_user', False)

    @property
    def python2(self):
        return self.config.get('python2')

    @property
    def python3(self):
        return self.config.get('python3')

    @property
    def virtualenv(self):
        return self.config.get('virtualenv')

    @property
    @cached('user_homedir')
    def user_homedir(self):
        # current user's home dir on the host
        if not self.per_user:
            return None
        
        if self.type == 'ssh':
            p = subprocess.check_output(['ssh', self.host, 'echo $HOME'])
            return p.decode('utf-8').strip()
        
        if self.type == 'container':
            p = subprocess.check_output(['ssh', self.host, 'docker exec {} echo $HOME'.format(self.container)])
            return p.decode('utf-8').strip()


    @property
    @cached('mordor_info')
    def mordor_info(self):
        if self.per_user:
            mordor_dir = os.path.join(self.user_homedir, 'mordor')
        else:
            mordor_dir = "/etc/mordor"
        
        mordor_config = os.path.join(mordor_dir, "mordor.json")
        if not self.has_file(mordor_config):
            return None
        
        # mordor is installed
        v = json.loads(self.read_text_file(mordor_config))
        if not v['root_dir'].startswith('/'):
            raise Exception("Mordor config's root_dir MUST be an absolute path")
        return v
    

    def has_file(self, filename):
        exit_code = self.execute("test -f {}".format(filename), to_raise=False)
        return exit_code == 0

    
    def initialize(self):
        # initialize host, any host need to be initialized once before it can be
        # used by mordor
        if self.per_user:
            mordor_dir = os.path.join(self.user_homedir, 'mordor')
        else:
            mordor_dir = "/etc/mordor"
        
        mordor_config = os.path.join(mordor_dir, 'mordor.json')
        if self.has_file(mordor_config):
            raise Exception("Mordor has been installed on this host, please cleanup first")

        mordor_info = {
            "root_dir": mordor_dir
        }
        context = json.dumps(mordor_info, indent=4, separators=(',', ': '))
       
        self.execute("mkdir", "-p", mordor_dir)
        self.upload_text(context, mordor_config)


    def execute(self, *args, to_raise=True):
        if self.type == 'ssh':
            return self._execute_ssh(*args, to_raise=to_raise)

        if self.type == 'container':
            return self._execute_container(*args, to_raise=to_raise)
        
        raise Exception("Unsupported host type: {}".format(self.type))

    
    def _execute_ssh(self, *args, to_raise=True):
        # execute a command on this host
        # when to_raise is True, if exit code is not 0, it will raise exception
        # when to_raise is False, it return the exit code
        new_args = ["ssh", "-t", "-q", self.host]
        new_args.extend(args)
        exit_code = subprocess.call(new_args, shell=False)
        if not to_raise:
            return exit_code
        if exit_code != 0:
            raise Exception("command \"{}\" failed with exit code: {}".format(" ".join(new_args), exit_code))


    def _execute_container(self, *args, to_raise=True):
        container_host = self.mordor.hosts[self.host]
        new_args = ["ssh", "-t", "-q", container_host.host, "docker", "exec", "-it", self.container]
        new_args.extend(args)
        exit_code = subprocess.call(new_args, shell=False)
        if not to_raise:
            return exit_code
        if exit_code != 0:
            raise Exception("command \"{}\" failed with exit code: {}".format(" ".join(new_args), exit_code))


    def download(self, remote_filename, local_filename):
        if self.type == 'ssh':
            return self._download_ssh(remote_filename, local_filename)

        if self.type == 'container':
            return self._download_container(remote_filename, local_filename)
        
        raise Exception("Unsupported host type: {}".format(self.type))

    def _download_ssh(self, remote_filename, local_filename):
        remote_file_location = "{}:{}".format(self.host, remote_filename)
        new_args = [
            "scp", "-q",
            remote_file_location,
            local_filename
        ]
        exit_code = subprocess.call(new_args)
        if exit_code != 0:
            raise Exception("Unable to copy: from {} to {}".format(remote_file_location, local_filename))

    def _download_container(self, remote_filename, local_filename):
        tmp_filename = os.path.join('/tmp', str(uuid.uuid4()))
        
        try:
            # copy: container --> ssh host
            exit_code = subprocess.call([
                'ssh', self.host, 
                "docker cp {}:{} {}".format(self.container, remote_filename, tmp_filename)
            ])
            a = "docker cp {}:{} {}".format(self.container, remote_filename, tmp_filename)
            if exit_code != 0:
                raise Exception("Unable to copy file {} to {} at {}".format(local_filename, self.host, remote_filename))

            # copy: ssh host to local
            remote_file_location = "{}:{}".format(self.host, tmp_filename)
            new_args = [
                "scp", "-q",
                remote_file_location,
                local_filename
            ]
            exit_code = subprocess.call(new_args)
            if exit_code != 0:
                raise Exception("Unable to copy: from {} to {}".format(remote_file_location, local_filename))
        finally:
            pass
            # exit_code = subprocess.call([
            #     'rm', '-f', tmp_filename
            # ])
            # if exit_code != 0:
            #     print("Warning: unable to delete temporary file {}".format(tmp_filename))


    def read_text_file(self, remote_filename):
        # handly function to read small remote files
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
            self.download(remote_filename, tmp.name)
            with open(tmp.name, "rt") as f:
                return f.read()
        finally:
            os.remove(tmp.name)
        

    def upload(self, local_filename, remote_filename):
        lf = os.path.expanduser(local_filename)
        lf = os.path.expandvars(lf)

        if self.type == 'ssh':
            return self._upload_ssh(lf, remote_filename)

        if self.type == 'container':
            return self._upload_container(lf, remote_filename)
        
        raise Exception("Unsupported host type: {}".format(self.type))

    def _upload_ssh(self, local_filename, remote_filename):
        new_args = [
            "scp", "-q",
            local_filename,
            "{}:{}".format(self.host, remote_filename)
        ]
        exit_code = subprocess.call(new_args)
        if exit_code != 0:
            raise Exception("Unable to copy file {} to {} at {}".format(local_filename, self.host, remote_filename))

    def _upload_container(self, local_filename, remote_filename):
        tmp_filename = os.path.join('/tmp', str(uuid.uuid4()))
        # copy to container host first
        new_args = [
            "scp", "-q",
            local_filename,
            "{}:{}".format(self.host, tmp_filename)
        ]
        exit_code = subprocess.call(new_args)
        if exit_code != 0:
            raise Exception("Unable to copy file {} to {} at {}".format(local_filename, self.host, remote_filename))
        
        # now copy to container
        try:
            exit_code = subprocess.call([
                'ssh', self.host, 
                "docker cp {} {}:{}".format(tmp_filename, self.container, remote_filename)
            ])
            if exit_code != 0:
                raise Exception("Unable to copy file {} to {} at {}".format(local_filename, self.host, remote_filename))
        finally:
            exit_code = subprocess.call([
                'rm', '-f', tmp_filename
            ])
            if exit_code != 0:
                print("Warning: unable to delete temporary file {}".format(tmp_filename))


    
    def upload_text(self, content, remote_filename):
        try:
            f = tempfile.NamedTemporaryFile(mode="wt", delete=False)
            f.write(content)
            f.close()
            self.upload(f.name, remote_filename)
        finally:
            os.remove(f.name)
