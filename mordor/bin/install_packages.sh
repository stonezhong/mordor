#!/bin/bash

# $1: mordor home dir
# $2: app name
# $3: version

source $1/venvs/$2-$3/bin/activate
pip -q install --upgrade pip
if [ -e $1/apps/$2/$3/requirements_pre.txt ]
then
    pip -q install -r $1/apps/$2/$3/requirements_pre.txt
fi
if [ -e $1/apps/$2/$3/requirements.txt ]
then
    pip -q install -r $1/apps/$2/$3/requirements.txt
fi
deactivate
