#!/bin/sh

# $1: mordor home dir
# $2: app name

source $1/venvs/$2/bin/activate
./main.py $1 $2
deactivate
