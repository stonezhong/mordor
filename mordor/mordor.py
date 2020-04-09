#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import argparse
import os
import json

from .host import Host
from .compartment import Compartment
from .deployment import Deployment
from .application import Application
from .configuration import Configuration
from .schema import validate_config

class Mordor(object):
    def __init__(self, base_dir, config_dir):
        # base_dir is the directory where mordor is installed
        # since we need to copy bin files to targets, we need to 
        # remember where we are launched off
        self.base_dir = base_dir
        self.config_dir = config_dir

        self.config = self.load_json('config.json')

        validate_config(self.config)

        self.hosts = {}
        for host_config in self.config["hosts"]:
            host_id = host_config["id"]
            if host_id in self.hosts:
                raise Exception("Duplicate host: {}".format(host_id))
            self.hosts[host_id] = Host(self, host_config)

        self.compartments = {}
        for compartment_config in self.config['compartments']:
            compartment_id = compartment_config['id']
            if compartment_id in self.compartments:
                raise Exception("Duplicate compartment: {}".format(compartment_id))
            self.compartments[compartment_id] = Compartment(self, compartment_config)

        self.applications = {}
        for application_config in self.config['applications']:
            application_id = application_config['id']
            if application_id in self.applications:
                raise Exception("Duplicate application: {}".format(application_id))
            self.applications[application_id] = Application(self, application_config)

        self.configurations = {}
        for configuration_config in self.config['configurations']:
            configuration_id = configuration_config['id']
            if configuration_id in self.configurations:
                raise Exception("Duplicate configuration: {}".format(configuration_id))
            self.configurations[configuration_id] = Configuration(self, configuration_config)

        self.deployments = {}
        for deployment_config in self.config['deployments']:
            deployment_id = deployment_config['id']
            if deployment_id in self.deployments:
                raise Exception("Duplicate deployment: {}".format(deployment_id))
            self.deployments[deployment_id] = Deployment(self, deployment_config)

    def load_json(self, filename):
        with open(os.path.join(self.config_dir, filename), "rt") as f:
            return json.load(f)

def main():
    parser = argparse.ArgumentParser(
        description='Mordor deployment tool for python'
    )
    parser.add_argument(
        "-c", "--config-dir", type=str, required=False, help="Specify the mordor config directory"
    )
    parser.add_argument(
        "-a", "--action", type=str, required=True, help="action. Could be init-target, stage, run, kill or status"
    )
    # cannot use -h, reserved by argparse
    parser.add_argument(
        "-o", "--host-id", type=str, required=False, help="Host id"
    )
    parser.add_argument(
        "-p", "--deployment-id", type=str, required=False, help="deployment name"
    )
    parser.add_argument(
        "-s", "--stage", type=str, required=False, help="stage"
    )
    parser.add_argument(
        "--update-venv",
        type=str,
        required=False,
        default="T",
        help="Specify T if you want to update virtualenv, F if not. Default is T"
    )
    args = parser.parse_args()
    config_dir = args.config_dir or os.path.expanduser("~/.mordor")

    mordor = Mordor(
        base_dir=os.path.abspath(os.path.dirname(__file__)),
        config_dir=config_dir
    )


    if args.action == "init-host":
        if not args.host_id:
            print("--host-id must be specified")
            return
        host = mordor.hosts.get(args.host_id)
        if host is None:
            raise Exception("Host {} does not exist!".format(args.host_id))

        host.initialize()
        return
    
    if args.action == "stage":
        deployment_id = args.deployment_id
        mordor.deployments[args.deployment_id].stage(args)
        return

    
    raise Exception("unrecognized action")



    # if args.action == "run":
    #     run_app(
    #         base_dir, config, args.app_name, 
    #         stage = args.stage, 
    #         host_name = args.host_name
    #     )
    #     return

    # if args.action == "kill":
    #     kill_app(
    #         base_dir, config, args.app_name, 
    #         stage = args.stage, 
    #         host_name = args.host_name
    #     )
    #     return

    # if args.action == "status":
    #     get_app_status(base_dir, config, args.app_name)
    #     return

    # raise Exception("unrecognized action")


if __name__ == '__main__':
    main()
