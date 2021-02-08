#!/bin/sh

if [ -z "${PROJECT_ROOT}" ]
then
    echo "Environment variable PROJECT_ROOT is not set"
    exit 1
fi

. ${PROJECT_ROOT}/.venv_test/bin/activate
export PYTHONPATH=${PROJECT_ROOT}/src
cd ${PROJECT_ROOT}
rm -rf ${PROJECT_ROOT}/docs/htmlcov
rm -rf ${PROJECT_ROOT}/htmlcov
python -m pytest ${PROJECT_ROOT}/tests --cov-report=html --cov=mordor
mv ${PROJECT_ROOT}/htmlcov ${PROJECT_ROOT}/docs