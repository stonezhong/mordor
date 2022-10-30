import subprocess
import os
from typing import Optional, List, Tuple
import tempfile


class HostConfig:
    """Represent configuration for a given host
    """

    name: str  # the unique name of the host we address this host, not necessary be the DNS name
    host_config: dict  # the config dictionary for this host

    def __init__(self, host_name: str, host_config: dict):
        self.host_config = host_config
        self.name = host_name

    @property
    def env_home(self) -> str:
        return self.host_config["env_home"]

    @property
    def ssh_host(self) -> str:
        return self.host_config["ssh_host"]

    @property
    def virtualenv(self) -> Optional[str]:
        return self.host_config.get("virtualenv")

    @property
    def python3(self) -> Optional[str]:
        return self.host_config.get("python3")

    @property
    def ssh_key_filename(self) -> Optional[str]:
        v = self.host_config.get("ssh_key_filename")
        if not v:
            return v
        return os.path.expanduser(v)

    @property
    def ssh_username(self) -> Optional[str]:
        return self.host_config.get("ssh_username")

    def path(self, *args) -> str:
        return os.path.join(self.env_home, *args)

    def execute_batch(self, lines: List[str]) -> None:
        """ Execute a bash batch file on this host

        :param lines: lines for the batch script
        :return: Nothing
        """
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
            subprocess.check_call(new_args, stdin=f)

    def execute(self, *args) -> None:
        """ Execute a one-line command on this host

        :param args: args for this script
        :return: Nothing
        """
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
        subprocess.check_call(new_args)

    def execute2(self, *args) -> Tuple[str, int]:
        """ Execute a script on this host, capture the output.

        :param args: args for this script
        :return: tuple, script stdout as string, and script exit code as integer
        """
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
        _ = p.wait()
        output, err = p.communicate()
        return output, err

    def upload_batch(self, local_path: str, remote_path: str) -> None:
        """ Upload an entire directory to the host

        :param local_path: the path to the directory which need upload
        :param remote_path: the destination path
        :return: Nothing
        """
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

        subprocess.check_call(new_args)

    def upload(self, local_path: str, remote_path: str) -> None:
        """ Upload a file to the host

        :param local_path: the path to the file which need upload
        :param remote_path: the destination path
        :return: Nothing
        """
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

        subprocess.check_call(new_args)
