class Target(object):
    # Values for TargetConfig.type
    TYPE_SSH = "ssh"
    TYPE_CONTAINER = "container"

    def __init__(self, name, config):
        self.config = config
        self.name = name

    @property
    def env_home(self):
        # This tells where is the root directory of mordor
        return self.host_config["env_home"]

    @property
    def type(self):
        return self.host_config["type"]

    @property
    def ssh_host(self):
        # the ssh host of the target
        # must have
        # for ssh ssh target, this is the the ssh host name
        # for the container target, this is the ssh host that
        # host the container, "localhost" is a special ssh host
        # that represent local machine
        return self.host_config["ssh_host"]

    @property
    def virtualenv(self):
        # optional, virtualenv path
        # ignored for python3, when it is python3, we use python -m venv
        return self.host_config.get("virtualenv")

    @property
    def python3(self):
        # optiona, python3 path
        return self.host_config.get("python3")

    @property
    def ssh_key_filename(self):
        # optional, ssh private key filename, can have environment variable
        # e.g. $HOME/.ssh/foo
        v = self.host_config.get("ssh_key_filename")
        if not v:
            return v
        return os.path.expanduser(v)

    @property
    def ssh_username(self):
        # optional, ssh username
        return self.host_config.get("ssh_username")

    # do we need this???
    # def path(self, *args):
    #     return os.path.join(self.env_home, *args)

    # execute a command in target
    # why we need 2 different execute??
    # def execute(self, *args):
    #     if self.ssh_key_filename:
    #         new_args = [
    #             "ssh",
    #             "-i",
    #             self.ssh_key_filename,
    #             "{}@{}".format(self.ssh_username, self.ssh_host)
    #         ]
    #     else:
    #         new_args = ["ssh", self.ssh_host]
    #     new_args.extend(args)
    #     subprocess.call(new_args)

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

    # def upload(self, local_path, remote_path):
    #     if self.ssh_key_filename:
    #         new_args = [
    #             "scp", "-q", "-i", self.ssh_key_filename,
    #             local_path,
    #             "{}@{}:{}".format(
    #                 self.ssh_username,
    #                 self.ssh_host, remote_path
    #             )
    #         ]
    #     else:
    #         new_args = [
    #             "scp", "-q",
    #             local_path,
    #             "{}:{}".format(self.ssh_host, remote_path)
    #         ]

    #     subprocess.call(new_args)
