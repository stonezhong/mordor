# Indexes
* [Introduction](#introduction)
* [Developers' guide](#developers-guide)
* [Install Mordor](#install-mordor)
* [Configuration](#configuration)
    * [Configuration directory](#configuration-directory)
    * [Configuration structure](#configuration-structure)
        * [Hosts section](#hosts-section)
        * [Deployments section](#deployments-section)
    * [Deal with Application Configurations](#deal-with-application-configs)
* [Sample Commands](#sample-commands)
    * [Initialize host](#initialize-host)
    * [Stage application](#stage-application)
    * [Run a command](#run-a-command)
* Examples
    * [Simple example](https://github.com/stonezhong/mordor/tree/master/samples/simple)
    * [Docker example](https://github.com/stonezhong/mordor/tree/master/samples/docker)
* [Environment ENV_HOME](#environment-env_home)
* [Application Structure](#application-structure)
* [File Structure on Host](#file-structure-on-host)

# Introduction

Mordor is a tool helps you to deploy your python application.

* 2022-11-05: Support for python 2 has been deprecated.
* 2022-12-16: Add SCP_OPTIONS to support MacOS Ventura 13.1 to use SCP instead of SFTP protocol, you can do `export SCP_OPTIONS="-O"`

# Developers' guide
This is for developers who want to adding features or fix bugs for mordor. Please see [For Developers](for_developers.md)

# Install mordor
Here is an example to install mordor from github
```bash
mkdir ~/.mordor_venv
python3 -m venv ~/.mordor_venv
source ~/.mordor_venv/bin/activate
python -m pip install pip setuptools --upgrade
python -m pip install wheel
python -m pip install git+https://github.com/stonezhong/mordor.git@master
# You can also do "python -m pip install mordor2"
```

# Configuration

## Configuration directory

Mordor deploys your application using configurations, and configurations are located in a directory.

Mordor locates the configuration directory with the following order:

1) You can specify it with `-c` option in command line.
2) You can specify it with environment variable `MORDOR_CONFIG_DIR`
3) Fall back to `~/.mordor`

* You can config mordor using either yaml or json format for your configuration file
    * For yaml format, you should provide config.yaml in configuration directory.
    * For json format, you should provide config.json in configuration directory.

## Configuration structure
Here is an example `config.json`:
```json
{
    "hosts": {
        "mordortest": {
            "ssh_host"  : "mordortest",
            "env_home"  : "/root/mordor",
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
            },
            "requirements": "requirements.txt",
        }
    }
}
```

or in yaml format `config.yaml`:
```yaml
hosts:
    mordortest:
        ssh_host: mordortest
        env_home: /root/mordor
        python3: /usr/bin/python3
deployments:
    sample_beta:
        name: sample
        stage: beta
        home_dir: /home/stonezhong/DATA_DISK/projects/mordor/sample
        deploy_to:
            - mordortest
        use_python3: Yes
        requirements: requirements.txt
        config:
            - foo.json: copy
```

### Hosts section
* In `hosts` section, you need to list all your hosts which you want to deploy to. The key is the host id, value is the configuration for the host, here are fields for value:
    * `python3`: Optional, please set python3 interrupter location, if you do not specify, mordor will assume it is `/usr/bin/python3`
    * `env_home`: Please set your mordor home directory.
    * `ssh_host` Optional, set your ssh hostname, if you do not specify, it will be the host id. Normally it should match what you have in your `~/.ssh/config` file, You need to make sure you can ssh to each machine without entering password, you can config your `~/.ssh/config` if needed

### Deployments section
* In `deployments` section, you need to list all the deployments you have, key is the deployment id, value is the configuration for the deployment, here are the fields for value:
    * `name` is the name of the application, if missing, then the deployment id becomes the application name
    * `stage` is the name of the stage, usually it is something like `beta`, `prod`, etc, but it can be anything, if missing, default to empty string
        * The same application can have as many stages as it supports, but each host can only deploy one stage. For example, you cannot deploy both beta and prod stage of the same application to the same host
    * `deploy_to` is a list of the host ids
    * `use_python3`: Must be true, otherwise, mordor will not deploy your application, default value is `True`.
    * `requirements`: filename for requirements, which specify the python package dependency, default to `requirements.txt`
    * the `config` section list all the config file you need to deploy to host

## Deal with application configs
When mordor looks for a config whose name is `config_name` to deploy on a host, it looks for it in the following order:
* host specific directory, in `{base_config_dir}/configs/{app_name}/{stage}/{host_name}/{config_name}`
* stage specific directory, in `{base_config_dir}/configs/{app_name}/{stage}/{config_name}`
* in config directory, in `{base_config_dir}/configs/{app_name}/{config_name}`

<b>This allows you to override config at stage level or host level.</b>

Mordor supports 3 types of config files:
* "copy" -- it simply copy the config file to the host
* "convert" -- the config is a python template string, you can use the following context variables:
```
config_dir: the application config directory on the host for the application
env_home  : the mordor home directory on the host
app_name  : the name of the application
```
* "template" -- the config is a jinja template string, you can use the following context variables:
```
host_name   : the host id
config_dir  : the application config directory on the host for the application
log_dir     : the log directory on the host for the application
data_dir    : the data directory on the host for the application
env_home    : the mordor home directory on the host
app_name    : the name of the application
```

Please visit [here](samples/) for a working examples.

# Sample commands
## Initialize host
Every host need to be initialized for mordor before you can stage application to it. Here is an example on how to initialize a host:
```bash
# initialize mordor on host mordortest, using config file from samples/simple/config
mordor init-host -c samples/simple/config -o mordortest
```

## Stage application
mordor allows you to stage application to all host belongs to a stage, or you can cherry pick host with -o options.
Here is an example to stage an application and setup the python virtual environment for the application on all the host for a given stage:
```bash
# stage application "sample" to "beta" stage
# On all the host machine belongs to the "beta" stage
#     the application will be copied to
#     configuration will be copied to
#     python virtual environment will be created
mordor stage -c samples/simple/config -p sample -s beta --update-venv
```
* In most cases, you just need to do `--update-venv` once, unless you update the requirements.txt, or first time you stage the application.
* Via application manifest, you can let mordor to trigger an command after the application is staged on a host, through the `on_stage` option, check the sample [here](samples/docker/src/manifest.yaml)

## Run a command
mordor allows you to run a commnad for an application, either on all host belongs to a stage or you can cherry pick host, your command is handled by dispatch.py in your application root directory.

```bash
# run command
# application is "sample", stage is "beta", command line is "foo xyz abc"
mordor run -c samples/simple/config -p sample -s beta --cmd "foo xyz abc"
```


# Application Structure

You can look at the [Samples](https://github.com/stonezhong/mordor/tree/master/samples)

* You need to have a manifest.json file, you normally want to bump the version if you make changes to your application.
* You need to have a requirements.txt in your application root directory which tells list of packages you need to install
* Optionally, if you want to support running remote command, you need to have a `dispatch.py`. When you run `mordor run ...`, `dispatch.py` owns the execution of the command. For details, see [dispatch.py](https://github.com/stonezhong/mordor/blob/master/samples/docker/src/dispatch.py) as example.

# Command line options
```
mordor \
  <action> \
  -c <mordor_config_base> \
  -o <host_id> \
  -p <app_name> \
  -s <stage> \
  [--update-venv] \
  [--config-only] \
  --cmd="<your command here>"

# action, could be `init-host`, `stage` or `run`
# -c, optional, you can specify the mordir configration directory location
# -o, specify the the host id.
#     for init-host, you must specify this
#     for stage or run, if missing, then the scope is all the host for the stage
# -p, the application name
# -s, the stage name, if missing, the stage name is empty string
# --cmd, the command you want to run when your action is "run"
# --update-venv, optional, when specified, mordor will update python virtual environment for the app
# --config-only, optional, when specified, mordor only update the application config.
```

# Environment ENV_HOME
After modor is initialized on target, target will have a environment variable `ENV_HOME`, set to the `env_home` setting from your host setting of your mordor config file.

# File Structure on Host
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
  |     +-- <application name>              pid directory for the application
  |             |
  |             +-- main.pid                An application may have many pid files.
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
