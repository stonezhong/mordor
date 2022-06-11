#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import pystache
from mordor import AppEnv

def main():
    app_env = AppEnv("sample")
    print(app_env)
    print("env_home = {}".format(app_env.env_home))
    print("app_name = {}".format(app_env.app_name))
    template = "Hi {{person}}!"
    context = {"person": "Mom"}
    print(pystache.render(template, context))

    foo_config = app_env.get_json_config("foo.json")
    print(foo_config)

if __name__ == '__main__':
    main()
