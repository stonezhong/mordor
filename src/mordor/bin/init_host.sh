#!/bin/bash

# $1: mordor home dir

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    printf "\n" >> ~/.bashrc
    printf "#Added for Mordor\n" >> ~/.bashrc
    printf "export ENV_HOME=$1\n" >> ~/.bashrc
    cat $1/bin/host_tools.txt >> ~/.bashrc
    printf "\n" >> ~/.bashrc
elif [[ "$OSTYPE" == "darwin"* ]]; then
    printf "\n" >> ~/.bash_profile
    printf "#Added for Mordor\n" >> ~/.bash_profile
    printf "export ENV_HOME=$1\n" >> ~/.bash_profile
    cat $1/bin/host_tools.txt >> ~/.bash_profile
    printf "\n" >> ~/.bash_profile
else
    echo "$OSTYPE is not supported. Please create an issue at https://github.com/stonezhong/mordor/issues if you want mordor to support your system"
fi
