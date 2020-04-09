import os
import json
import uuid
import pystache

from .configuration import AnonymousConfiguration

class Deployment(object):
    def __init__(self, mordor, config):
        self.mordor = mordor
        self.config = config


    @property
    def id(self):
        return self.config['id']


    @property
    def compartments(self):
        # list of compartments
        return [
            self.mordor.compartments[compartment_id] for compartment_id in self.config['compartments']
        ]

    @property
    def configurations(self):
        # list of configurations
        ret = []
        for item in self.config['configurations']:
            if isinstance(item, str):
                configuration = self.mordor.configurations[item]
            else:
                configuration = AnonymousConfiguration(self.mordor, item)
            ret.append(configuration)

        return ret

    @property
    def application(self):
        return self.mordor.applications[self.config['application']]
    

    @property
    def use_python(self):
        # as of today (2020-04-07), mainstream should be using python3
        return self.config.get('use_python', 'python3')

    def stage(self, args):
        # args is the command line arguments
        for compartment in self.compartments:
            self.stage_to(compartment, args)


    def stage_to(self, compartment, args):
        self.application.build(compartment, args)

        instance_id = str(uuid.uuid4())
        # now create runtime environment
        host = compartment.host
        remote_root_dir = host.mordor_info['root_dir']

        remote_compartments_dir = os.path.join(remote_root_dir, "compartments", compartment.id)
        host.execute("mkdir", "-p", remote_compartments_dir)
        host.execute("mkdir", "-p", os.path.join(remote_compartments_dir, 'data', self.id))
        host.execute("mkdir", "-p", os.path.join(remote_compartments_dir, 'logs', self.id))

        host.execute("mkdir", "-p", os.path.join(remote_compartments_dir, 'deployments', self.id))

        remote_deployment_dir = os.path.join(os.path.join(remote_compartments_dir, 'deployments', self.id))
        host.execute("mkdir", "-p", os.path.join(remote_deployment_dir, 'instances'))

        remote_instance_dir = os.path.join(remote_deployment_dir, 'instances', instance_id)
        host.execute("mkdir", "-p", remote_instance_dir)

        # create configuration dir
        remote_instance_configuration_dir = os.path.join(remote_instance_dir, "config")
        host.execute("mkdir", "-p", remote_instance_configuration_dir)
        for configuration in self.configurations:
            if configuration.type == 'raw':
                host.upload(
                    configuration.location, 
                    os.path.join(remote_instance_configuration_dir, configuration.name)
                )
            if configuration.type == 'template':
                with open(configuration.location, 'rt') as f:
                    template = f.read()
                content = pystache.render(template, {
                    'env_home': remote_instance_dir,
                    'log_dir': os.path.join(remote_compartments_dir, 'logs', self.id)
                })
                host.upload_text(
                    content, 
                    os.path.join(remote_instance_configuration_dir, configuration.name)
                )
            else:
                raise Exception("configuration type {} is not recognized".format(configuration.type))

        # link it to the application
        host.execute(
            "ln", 
            "-s", 
            os.path.join(
                remote_root_dir, 'applications', self.application.id, 
                self.application.manifest['version'], 'src'
            ),
            os.path.join(remote_instance_dir, 'src')
        )

        host.execute(
            "ln", 
            "-s", 
            os.path.join(
                remote_root_dir, 'compartments', compartment.id, 'data', self.application.id
            ),
            os.path.join(remote_instance_dir, 'data')
        )

        host.execute(
            "ln", 
            "-s", 
            os.path.join(
                remote_root_dir, 'compartments', compartment.id, 'logs', self.application.id
            ),
            os.path.join(remote_instance_dir, 'logs')
        )

        if self.use_python == 'python2':
            host.execute(
                "ln", 
                "-s", 
                os.path.join(
                    remote_root_dir, 'applications', self.application.id, 
                    self.application.manifest['version'], 'venv_p2'
                ),
                os.path.join(remote_instance_dir, 'venv')
            )
        elif self.use_python == 'python3':
            host.execute(
                "ln", 
                "-s", 
                os.path.join(
                    remote_root_dir, 'applications', self.application.id, 
                    self.application.manifest['version'], 'venv_p3'
                ),
                os.path.join(remote_instance_dir, 'venv')
            )
        else:
            print("Unsupported python version: {}".format(self.use_python))
        
        remote_instance_current_dir = os.path.join(remote_deployment_dir, 'current')
        host.execute("rm", "-f", remote_instance_current_dir)
        host.execute(
            "ln", 
            "-s", 
            remote_instance_dir,
            remote_instance_current_dir
        )
