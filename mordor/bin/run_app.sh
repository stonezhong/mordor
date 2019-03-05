#!/bin/bash

# $1: mordor home dir
# $2: app name

cd $1/apps/$2/current
./run.sh $1 $2 > $1/logs/$2/output_$(date "+%Y_%m_%d_%H_%M_%S").log 2>&1 &
echo $! > $1/pids/$2.pid
