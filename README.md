# Purpose

If you have python based application, need to deploy to a fleet of machines and need to constantly update these application, mordor is the right tool for you. You can

* Deploy your python application to the host fleet
* Start and stop your python application on the fleet
* Update your python application on the fleet.

# config
The config file describes the deployment. The default location of the config file is `~/.mordor/config.json`, however, you can override it with `-c` option in command line.

There are few sections in the config file.

<details>
<summary>summary</summary>


```
{
    "hosts": [
        host1, host2, ...
    ],
    "compartments": [
        compartment1, compartment2, ...
    ],
    "applications": [
        application1, application2, ...

    ],
    "configurations": [
        configuration1, configuration2, ...
    ],
    "deployments": [
        deployment1, deployment2, ...
    ]

}
```
</details>

<details>
<summary>host</summary>

| field       | required  | description           | example    |
|-------------|-----------|-----------------------|------------|
| id          | Yes       | Unique id of the host | "myserver" |
| type        | Yes       | "ssh" or "container"t | "ssh"      |
| host        | Yes       | ssh name for the target, either the host itself or the host that the container runs in | "www.myserver.com" |
| container   | Optional  | the container name    | "test1"    |
| per_user    | Yes       | false if mordor is installed system wide or per user. | false |
| python2     | Optional  | python 2.x binary name | "python"  |
| python3     | Optional  | python 3.x binary name | "python3" |
| virtualenv  | Optional  | virtualenv binary name | "virtualenv-2" |

* If type is `"ssh"`, it means you can connect to it via ssh, the ssh target's name is specified by `host` field. Check your `~/.ssh/config` file.
* If type is `"container"`, it means the host is a container, you should be able to connect to the machine which this container lives in via ssh, the machine's target name is specified by `host` field. Check your `~/.ssh/config` file.
* If type is `"container"`, the `container` field specifies the container name.
* If per_user is `true`, then mordor is installed at `/etc/mordor`, otherwise, mordor is installed at `~/mordor` on the target, current user depend on your `~/.ssh/config`'s setting.
* The binary name for python 2 is different in different systems, it could be `python`, or could be `python2`, we make it configurable. If python 2 is not installed, you can omit this field.
* The binary name for python 3 is different in different systems, it could be `python`, or could be `python3`, we make it configurable. If python 3 is not installed, you can omit this field.
* We need to run virtualenv to create virtual environment, when python 3 is used, we will run virtualenv as a module, however, when python 2 is sued, we need to run virtualenv command, the virtualenv field tells the binary name for virtualenv. You can omit this field if python 2 is not installed. 
</details>

<details>
<summary>compartment</summary>

| field       | required  | description                  | example            |
|-------------|-----------|------------------------------|--------------------|
| id          | Yes       | Unique id of the compartment | "prod"             |
| host        | Yes       | the id of the `host` this compartment lives in | "myserver" |
</details>

<details>
<summary>application</summary>

| field           | required  | description                      | example            |
|-----------------|-----------|----------------------------------|--------------------|
| id              | Yes       | Unique id of the application     | "myserver"         |
| home_dir        | Yes       | The root of the source code of the application | "~/projects/myserver" |
| support_python2 | Optional  | Does this application support python 2? | false |
| support_python3 | Optional  | Does this application support python 3? | true |

* If your application does not support python 2, you can omit `support_python2` field
* If your application does not support python 3, you can omit `support_python3` field
</details>

<details>
<summary>compartment</summary>

| field       | required  | description                  | example            |
|-------------|-----------|------------------------------|--------------------|
| id          | Yes       | Unique id of the compartment | "prod"             |
| host        | Yes       | the id of the `host` this compartment lives in | "myserver" |
</details>

<details>
<summary>configuration</summary>

| field           | required  | description                        | example              |
|-----------------|-----------|------------------------------------|----------------------|
| id              | Yes       | Unique id of the configuration     | "beta_server_config" |
| location        | Yes       | the filename for the configuration | "~/.configurations/beta_server_config.json" |
| type            | Yes       | is it a raw config file or a template ? | "raw"    |

* If type is `"raw"`, the file will be copied over to the host
* If type is `"template"`, the file is a template, the variable in the template will be replaced before copy over.
</details>

<details>
<summary>deployment</summary>

| field           | required  | description                         | example                  |
|-----------------|-----------|-------------------------------------|--------------------------|
| id              | Yes       | The Unique id of the deployment     | "beta_server_deployment" |
| application     | Yes       | The id of the application to deploy | "myserver"               |
| compartment     | Yes       | The id of the compartment for the deployment destination | "prod"   |
| use_python      | Yes       | specify which python version we are deploying, either "python2" or "python3" | "python2"   |
| configurations  | Optional  | list of mixed, see comment <1>      | ["beta_server_config"] |

* <1>: the list item could be a configuration id, such as "beta_server_config"
* <2>: the list item could be an anonymous configuration, such as below
```
{
    "location": "~/configs/beta_aws.json",
    "type": "raw"
}
```
</details>

Here is an example of the [config file](sample/config.json)

# Target Host file structure

<details>
<summary>details</summary>

```
MORDOR_ROOT
  |
  +-- applications
  |     |
  |     +-- application_id1
  |           |
  |           +-- version1
  |           |     |
  |           |     +-- src
  |           |     |
  |           |     +-- venv_p2
  |           |     |
  |           |     +-- venv_p3
  |           |
  |           +-- version2
  |                 |
  |                 +-- src
  |                 |
  |                 +-- venv_p2
  |                 |
  |                 +-- venv_p3
  |
  +-- compartments
        |
        +-- compartment_id1
        |     |
        |     +-- data
        |     |     |
        |     |     +-- deployment_id1
        |     |     |
        |     |     +-- deployment_id2
        |     |
        |     +-- logs
        |           |
        |           +-- deployment_id1
        |           |
        |           +-- deployment_id2
        |
        +-- deployments
              |
              +-- deployment_id1
                    |
                    +-- instances
                    |     |
                    |     +-- deployment_instance_id1
                    |     |     |
                    |     |     +-- config
                    |     |     |
                    |     |     +-- data     ==> symlink to deployment's data dir
                    |     |     |
                    |     |     +-- logs     ==> symlink to deployment's logs dir
                    |     |     |
                    |     |     +-- src      ==> symlink to application's particular version's src dir
                    |     |     |
                    |     |     +-- venv     ==> symlink to application's particular version's venv_p2 or venv_p3 dir
                    |     |
                    |     +-- deployment_instance_id2
                    |           |
                    |           +-- config
                    |           |
                    |           +-- data     ==> symlink to deployment's data dir
                    |           |
                    |           +-- logs     ==> symlink to deployment's logs dir
                    |           |
                    |           +-- src      ==> symlink to application's particular version's src dir
                    |           |
                    |           +-- venv     ==> symlink to application's particular version's venv_p2 or venv_p3 dir
                    |
                    +-- current              ==> symlink to the most recent instances
```
</details>



# FAQs
<details>
<summary>When you deploy an app, what is the version?</summary>

Each application should have a manifest.json file in the root of the source code directory. It looks like:
```
{
    "version": "0.0.1"
}
```

Once you make any change to your application, you need to bump the version. And then your application will be deployed to the new location without overwriting the existing running app on the host.

Note, a given version of app's code can be shared by many deployments on that host. It is also possible there are many deployments with each use different version of the same app. For example, you can have a production deployment running a stable version while the beta version running the most recent version of the code.

Do not update your code without bumping the version, in most cases, it is a bad idea, unless you are running a dev box and you are sure your deployment is the only deployment uses that code.
</details>

<details>
<summary>What happened to data and logs directory of my deployment when a deployment happened?</summary>

You log directory will not change, and the files in that directory will still be there.

You data directory will not change, and the files in that directory will still be there.

So you can expect your data will be kept cross deployments, but in general, keep state in local machine is not a good idea, you shuold consider to make your deployment stateless and applcation store state in the cloud.
</details>

<details>
<summary>What does stage command do?</summary>

Basically, it stages your code into the target deployment.
* If will copy your code to the host
* It will create a virtual environment if needed
* It will copy your configuration to the target deployment if you specify configurations.
* Every `stage` will create a deployment instance, which is a runtime environment that bundles the config, venv, src, logs and data directory. A deployment instance is very light-weight since except config directory, all otherr directory are simply symlinks.

<b>You need to manually stop your application, do the stage and start your application</b>
</details>
