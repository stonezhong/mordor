#!/bin/bash

# $1: mordor home dir
# $2: app name
# $3: cmd

source $1/venvs/$2/bin/activate
cd $1/apps/$2/current

python -u $3 --env_home $1 --app_name $2 > $1/logs/$2/output_$(date "+%Y_%m_%d_%H_%M_%S").log 2>&1 &
echo $! > $1/pids/$2.pid
