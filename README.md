# Indexes
* [Introduction](#introduction)
* [Config](#config)
    * [Config directory](#config-directory)
    * [Config structure](#config-structure)
* [Sample Commands](#sample-commands)
    * [Init target host](#init-target-host)
    * [Stage application to target](#stage-application-to-target)
    * [Run a command on target](#run-a-command-on-target)
* [Environment ENV_HOME](#environment-env_home)
* [Application Structure](#application-structure)
* [Target host mordor file structure](#target-host-mordor-file-structure)

# Introduction

Mordor is a tool helps you to deploy your python project.

# Config

## Config directory

Mordor locates the config directory with the following order:

1) The config directory you specified after `-c` option
2) Specified by environment variable `MORDOR_CONFIG_DIR`
3) Uses `~/.mordor`


## Config structure
Here is an example:
```json
{
    "hosts": {
        "mordortest": {
            "ssh_host"  : "mordortest",
            "env_home"  : "/root/mordor",
            "virtualenv": "/usr/bin/virtualenv",
            "python3"   : "/usr/bin/python3"
        }
    },
    "deployments": {
        "sample_beta": {
            "name"        : "sample",
            "stage"       : "beta",
            "home_dir"    : "/home/stonezhong/DATA_DISK/projects/mordor/sample",
            "deploy_to"   : [ "mordortest" ],
            "use_python3" : true,
            "config"      : {
                "foo.json": "copy"
            }
        }
    }
}
```

* In `hosts` section, you need to list all your target machine which you want to deploy to.
    * You need to make sure you can ssh to each machine without entering password, you can config your `~/.ssh/config` if needed
    * If your target machine support python3, you need to specify python3 location
    * `env_home` is the root path for mordor, normally you want to point it to a large disk, for example `/mnt/mordor`
    * `ssh_host` is the name of the host when you do ssh, normally it should match what you have in your `~/.ssh/config` file
* In `deployments` section, you list all the deployments you want to deploy
    * `name` is the name of the application, if missing, then the deployment name becomes the application name
    * `stage` is the name of the stage, usually it is something like `beta`, `prod`, etc, but it can be anything
        * The same application can have as many stages as it can, but each target can only deploy one stage. For example, you cannot deploy both beta and prod stage of the same app to the same target
    * `deploy_to` is a list of the target's name
    * `use_python3`: set to true if your app need python3
    * the `config` section list all the config file you need to deploy to the target
    * when looking for config file xyz, mordor lookup the config with the following order
        * `<base_config_dir>/configs/<app_name>/<stage>/xyz`
        * `<base_config_dir>/configs/<app_name>/xyz`
    * `stage`: the stage of this deployment, if missing, then stage is ""


# Sample commands
## Init target host
<details>
<summary>Initialize target host</summary>

```bash
# initialize mordor on target host mordortest, using config file from /home/stonezhong/testmordor/.mordor
mordor -c /home/stonezhong/testmordor/.mordor -a init-host -o mordortest
```
</details>

## Stage application to target
<details>
<summary>Stage application to target</summary>

```bash
# stage application sample to beta stage
# the application will be copied to the target machine
# configuration will be copied to the target machine
# python virtual environment will be created on target machine
mordor -c /home/stonezhong/testmordor/.mordor -a stage -p sample -s beta --update-venv
```
</details>

## Run a command on target
<details>
<summary>Run a command on target</summary>

```bash
# run command
# application is "sample", stage is "beta", command is "foo" with option "xyz abc"
mordor -c /home/stonezhong/testmordor/.mordor -a run -p sample -s beta -cmd foo -co "xyz abc"
```
</details>

# Application Structure

You can look at the [Sample](https://github.com/stonezhong/mordor/tree/master/sample)

* You need to have a manifest.json file, you normally want to bump the version if you make changes to your application.
* You need to have a requirements.txt in your application root which tells list of packages you need to install
* Optionally, if you want to support running remote command, you need to have a `dispatch.py`. When you run `mordor -a run ...`, `dispatch.py` owns the action on the command. For details, see [dispatch.py](https://github.com/stonezhong/mordor/blob/master/sample/dispatch.py) as example.

# Command line options
```
mordor \
  -c <mordor_config_base> \
  -a <action> \
  -o <target_name> \
  -p <app_name> \
  -s <stage> \
  [--update-venv] \
  [--config-only] \
  -cmd="<your command here>"

# -c, optional, you can specify the mordir configration directory location
# -a, action, could be `init-host`, `stage` or `run`
# -o, specify the the target machine.
#     for init-host, you must specify this
#     for stage or run, if missing, then the scope is all the target for the stage
# -p, the application name
# -s, the stage name, if missing, the stage name is empty string
# -cmd, the command you want to run when your action is "run"
# --update-venv, optional, when specified, mordor will update python virtual environment for the app
# --config-only, optional, when specified, mordor only update the application config.
```

# Environment ENV_HOME
After modor is initialized on target, target will have a environment variable `ENV_HOME`, set to the `env_home` setting from your host setting of your mordor config file.

# Target host mordor file structure
```
$ENV_HOME
  |
  +-- apps                                  Home directory for all applications
  |     |
  |     +-- <application name>              Home directory for an application
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
  |            |
  |            +-- config1                  depends on your deployment's `config` settings
  |            |
  |            +-- config2
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
  |     |
  |     +-- <application_name>              A symlink points to the current version
  |
  +-- data
  |     |
  |     +-- <application name>
  |
  +-- temp                                  Temporary directory

```

Note, `stage` action does not touch the data directory, it only update code and config. So data is kept the same after your `stage` action.
