#!/bin/sh

if [ -z "${PROJECT_ROOT}" ]
then
    echo "Environment variable PROJECT_ROOT is not set"
    exit 1
fi

rm -rf ${PROJECT_ROOT}/docs/pydocs
mkdir ${PROJECT_ROOT}/docs/pydocs

. .venv_build/bin/activate
cd ${PROJECT_ROOT}/docs/pydocs

PYTHONPATH=${PROJECT_ROOT}/src python -m pydoc -w \
    mordor
