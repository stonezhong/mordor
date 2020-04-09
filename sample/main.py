#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import print_function

import logging, logging.config
import os

DEPLOYMENT_BASE = os.path.dirname(os.getenv('PWD'))
logging.config.fileConfig(os.path.join(DEPLOYMENT_BASE, 'config', 'log.ini'))
logger = logging.getLogger(__name__)
 
import pystache

def main():
    
    logger.info('Hello')

    # print('hello {}'.format(DEPLOYMENT_BASE))

    # app_env = AppEnv.get()
    # print("env_home = {}".format(app_env.env_home))
    # print("app_name = {}".format(app_env.app_name))
    # template = "Hi {{person}}!"
    # context = {"person": "Mom"}
    # print(pystache.render(template, context))

if __name__ == '__main__':
    main()
