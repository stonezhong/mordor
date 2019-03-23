#!/bin/bash

# $1: mordor home dir
# $2: app name
if [ -e $1/pids/$2.pid ]; then
    ps $(cat $1/pids/$2.pid) > /dev/null
    if [ $? -eq 0 ] ; then 
        echo "Running: $(cat $1/pids/$2.pid)"
    elif [ $? -eq 1 ] ; then
        echo "Not running"
    else
        echo "Unknown"
    fi
else
    echo "Not running"
fi

