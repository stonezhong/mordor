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
        return self.host_config.get("ssh_host", self.name)

    @property
    def python3(self) -> Optional[str]:
        return self.host_config.get("python3", "/usr/bin/python3")

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

            new_args = ["ssh", "-q", self.ssh_host]
            subprocess.check_call(new_args, stdin=f)

    def execute(self, *args) -> None:
        """ Execute a one-line command on this host

        :param args: args for this script
        :return: Nothing
        """
        new_args = ["ssh", "-q", "-t", self.ssh_host]
        new_args.extend(args)
        subprocess.check_call(new_args)

    def execute2(self, *args) -> Tuple[str, int]:
        """ Execute a script on this host, capture the output.

        :param args: args for this script
        :return: tuple, script stdout as string, and script exit code as integer
        """
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
        new_args = [
            "scp", "-q",
            local_path,
            "{}:{}".format(self.ssh_host, remote_path)
        ]
        subprocess.check_call(new_args)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "env_home": self.env_home,
            "ssh_host": self.ssh_host,
        }
