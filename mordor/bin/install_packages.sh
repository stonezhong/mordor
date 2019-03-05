#!/bin/bash

# $1: mordor home dir
# $2: app name
# $3: version

source $1/venvs/$2-$3/bin/activate
pip install --upgrade pip
pip install -r $1/apps/$2/$3/requirements.txt
deactivate
