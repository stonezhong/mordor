#!/bin/bash

# $1: mordor home dir
# $2: app name

kill $(cat $1/pids/$2.pid)
