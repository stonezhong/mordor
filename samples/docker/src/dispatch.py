#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
from mordor import prepare_for_docker, AppEnv


def main():
    parser = argparse.ArgumentParser(
        description='Dispatch Tool'
    )
    parser.add_argument(
        "action", type=str, help="Specify action",
        choices=['on_stage'],
        nargs=1
    )
    args = parser.parse_args()
    action = args.action[0]

    app_env = AppEnv("sample")
    context = app_env.get_config("_deployment.json")
    prepare_for_docker("sample", context)

if __name__ == '__main__':
    main()
