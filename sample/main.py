#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import print_function

import logging
import os

DEPLOYMENT_BASE = os.path.dirname(os.getenv('PWD'))

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)
 
# Handler
handler = logging.FileHandler(os.path.join(DEPLOYMENT_BASE, 'logs', 'app.log'))
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)
 
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
