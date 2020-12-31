#!/bin/bash

# $1: mordor home dir
# $2: app name
# $3: cmd
# $4: cmd-options

source $1/venvs/$2/bin/activate
cd $1/apps/$2/current

python -u dispatch.py $(echo $4|base64 --decode)
