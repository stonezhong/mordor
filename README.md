# Purpose #

If you have python based application, need to deploy to a fleet of machines and need to constantly update these application, mordor is the right tool for you. You can

* Deploy your python application to the host fleet
* Start and stop your python application on the fleet
* Update your python application on the fleet.

# config #
You need to have a local config file placed in `~/.mordor/config.json`. Here is an example:
```
{
    "hosts": {
        "localhost": {
            "ssh_host": "localhost",
            "home_dir": "/Users/shizhong/mordor",
            "virtualenv": "/usr/local/bin/virtualenv"
        },
        "mylinux": {
            "ssh_host": "mylinux",
            "home_dir": "/home/SHIZHONG/mordor",
            "virtualenv": "/usr/bin/virtualenv"
        }
    },
    "applications": {
        "sample": {
            "home_dir"  : "/Users/shizhong/projects/sample",
            "deploy_to" : [ "mylinux", "localhost" ],
            "config": {
                "config": "convert",
                "oci_api_key.pem": "copy"
            }
        }
    }
}
```
It means:
* You have a host called localhost
    * Mordor home directory is `/Users/shizhong/mordor`
    * virtualenv command is at `/usr/local/bin/virtualenv` (it is a macbook)
    * `ssh_host` field tells the hostname you use in ssh, you can config it in `~/.ssh/config`
* You have a host called mylinux
    * Mordor home directory is `/Users/SHIZHONG/mordor`
    * virtualenv command is at `/usr/bin/virtualenv` (it is a Oracle Linux)
    * `ssh_host` field tells the hostname you use in ssh, you can config it in `~/.ssh/config`
* You have an application called `sample`
    * Your application code is at `/Users/shizhong/projects/sample` on your machine
    * This application will be deployed to `mylinux` and `localhost` (2 machines)
    * config file `~/.mordor/config/sample/config` will be copied to target machine at `configs/sample/config`
        * You can use variable in this file, variable will be replaced
    * config file `~/.mordor/config/sample/oci_api_key.pem` will be coped to target machine at `configs/sample/oci_api_key.pem`

# Host overview #
You need to config ssh so you do not need to enter password when you ssh to host on your fleet.

## Before initialization ##
On host of your fleet, 
* You need to make sure python 2.x is installed. For most of the Linux dist and mac, this is true.
* You need to install virtualenv and pip.
* You need to add entry in hosts sections for every machine you managed.

## Initialization ##
Run `mordor.py -a init_host --host_name <hostname>` to initialize your host. The host only need to be initialized once normally.
Here is a layout of your host directory structure:
```
<Mordor Home Directory>
  |
  +-- apps                                  Home directory for all applications
  |     |
  |     <application name>                  Home directory for an application
  |         |
  |         +-- <version 1>                 Directory for version 1 of application
  |         |
  |         +-- <version 2>                 Directory for version 2 of application
  |         |
  |         +-- current                     A symlink to the current version
  |
  +-- bin                                   Some tools used by mordor
  |
  +-- configs                               Home directory for configs for all applications
  |     |
  |     +-- <application name>              Config for an application
  |
  +-- logs                                  Home directory for logs for all applications
  |     |
  |     +-- <application name>              Logs for an application
  |
  +-- pids                                  Directory for pid for each application
  |     |
  |     +-- <application name>.pid          pid for the latest run of an application
  |
  +-- venvs                                 Home for virtual envs for all application
  |     |
  |     +-- <application name>_<version>    Virtual env for a given application with given version
  |
  +-- temp                                  Temporary directory
```

# Stage #
You can run command `mordor.py -a stage --app_name <application_name>` to stage application to all the host the app is suppose to deploy
* In `config.json`, the `deploy_to` tells the list of host it will deploy to
* In application's home directory, there is a file `manifest.json`, it looks like below
```
{
    "version": "0.0.1"
}
```
The version tells the version of the app, 
* On each deployable host, app's code will be copied over to `apps/<application_name>/<version>` directory
    * A sym link will be crate, so you can use `app/<application_name>/current/` as the current version
* On each deployable host, virtualenv will be created, all required package will be installed.
    * it looks for `requirements.txt` in your application directory for packages to install
    * on host, virtual env is a `venvs/<application_name>-<version>`
    * a symlink will be created in `venvs/<application_name>`
* All the config file will also be copied over
    * config file should be stored at `~/.mordor/configs/<application_name>`
    * the `config` section of application in `config.json` will tell what file need to be copied over
    * `copy` means simply copy over, `convert` means you can use variable like `home_dir` and `app_name` in your config file.

# run #
You can run `mordor.py -a run --app_name <application_name>` to run the application, all host deployed will run your application

# Application #
* You need to put a file `requirements.txt` to tell your applications dependency
* You need to provide a `run.sh` command, this command will be called to launch your program

To see an example, see [sample](./sample)