#!/bin/sh

if [ -z "${PROJECT_ROOT}" ]
then
    echo "Environment variable PROJECT_ROOT is not set"
    exit 1
fi

cd ${PROJECT_ROOT}
rm -rf build dist src/mordor2.egg-info
. .venv_build/bin/activate
python setup.py sdist bdist_wheel --universal
