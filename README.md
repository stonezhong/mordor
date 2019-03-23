# Purpose

If you have python based application, need to deploy to a fleet of machines and need to constantly update these application, mordor is the right tool for you. You can

* Deploy your python application to the host fleet
* Start and stop your python application on the fleet
* Update your python application on the fleet.

# config
You need to have a local config file placed in `~/.mordor/config.json`. Here is an example:
```
{
    "hosts": {
        "localhost": {
            "ssh_host"  : "localhost",
            "home_dir"  : "/Users/shizhong/mordor",
            "virtualenv": "/usr/local/bin/virtualenv",
            "python3"   : "/usr/local/bin/python3"
        },
        "mylinux": {
            "ssh_host"  : "mylinux",
            "home_dir"  : "/home/SHIZHONG/mordor",
            "virtualenv": "/usr/bin/virtualenv",
            "python3"   : "/usr/bin/python3"
        },
        "test3": {
            "ssh_host": "test3.deepspace.local",
            "home_dir": "/root/mordor",
            "virtualenv": "/usr/bin/virtualenv",
            "ssh_key_filename": "~/.runtime/cloudconfig/home",
            "ssh_username": "root",
            "python3": "/usr/bin/python36"
        }
    },
    "applications": {
        "sample": {
            "home_dir"    : "/Users/shizhong/projects/sample",
            "deploy_to"   : [ "mylinux", "localhost" ],
            "use_python3" : true,
            "config"      : {
                "config"         : "convert",
                "oci_api_key.pem": "copy"
            }
        }
    }
}
```

## Host Config

* In "hosts", key is host name, value is host config

### ssh_host
You should be able to ssh to the target host using their ssh_host attribute as host name without entering password.
You may need to use `ssh-add` command and config your `~/.ssh/config`

### ssh_key_filename
If you need to use a private key to connect to ssh server, you can specify the key filename here

### ssh_username
You must provide this if you specify ssh_key_filename. It represent the ssh username

### home_dir
This specify the home directory for mordor.

### virtualenv
This specify the full path for virtualenv command

### python3
This specify the full path for python3. You do not need to have this attribute if you do not plan to use python3.

## Application configs

* In applications. key is application name, value is application config

### home_dir
This specify where is the application's home directory.

### deploy_to
This is an array, tells list of host the application will deploy to.

### use_python3
If true, then this application uses python3. Default is false

### cmd
optional. Specify a command when you run an application. If can be a bash shell script or a python script. A bash shell script's filename must end with `.sh`, a python script's filename must end with `.py` 

# Host 
Before a host become usable for mordor, you need to
* Add host config to your `~/.mordor/config.json`
* Run `mordor -a init_host --host_name <hostname>` to initialize your host

## Before initialization
On host of your fleet, 
* You need to make sure python 2.x is installed. For most of the Linux dist and mac, this is true.
* If you need to deploy application that uses python3 on this host, you need to install python3
  * And set python3 in host config  
* You need to install virtualenv and pip.
* You need to add entry in hosts sections for every machine you managed.

## Initialization
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
  +-- data
  |     |
  |     +-- <application name>
  |
  +-- temp                                  Temporary directory
```

# Stage Your Application
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

# run
You can run `mordor.py -a run --app_name <application_name>` to run the application, all host deployed will run your application. It will invoke the command you specify in the application's cmd config, or using "run.sh" if missing.

# Application Requirement
* You need to put a file `requirements.txt` to tell your applications dependency
* You need to provide a `run.sh` command, this command will be called to launch your program

To see an example, see [sample](./sample)
