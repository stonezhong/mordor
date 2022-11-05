#!/bin/bash

# $1: mordor home dir
# $2: app name
# $3: cmd

export ENV_HOME=$1
source $1/venvs/$2/bin/activate
cd $1/apps/$2/current

python -u dispatch.py $(echo $3|base64 --decode)
