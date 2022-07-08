#!/bin/bash

# $1: mordor home dir
# $2: app name
# $3: version
# $4: requirement.txt filename

source $1/venvs/$2-$3/bin/activate
python -m pip -q install --upgrade pip setuptools
python -m pip -q install wheel

if [ -e $1/apps/$2/$3/requirements_pre.txt ]
then
    python -m pip -q install -r $1/apps/$2/$3/requirements_pre.txt
fi
if [ -e $1/apps/$2/$3/$4 ]
then
    python -m pip -q install -r $1/apps/$2/$3/$4
fi
deactivate
