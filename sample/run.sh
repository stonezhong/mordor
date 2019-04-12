#!/bin/bash

# $1: mordor home dir
# $2: app name

source $1/venvs/$2/bin/activate
./main.py --env_home $1 --app_name $2
deactivate
