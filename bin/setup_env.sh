#!/bin/sh

if [ -z "${PROJECT_ROOT}" ]
then
    echo "Environment variable PROJECT_ROOT is not set"
    exit 1
fi

echo "##################################################"
echo "#"
echo "# setup python virtual environment for build env"
echo "#"
echo "##################################################"

rm -rf mkdir ${PROJECT_ROOT}/.venv_build
mkdir ${PROJECT_ROOT}/.venv_build
python3 -m venv ${PROJECT_ROOT}/.venv_build
. ${PROJECT_ROOT}/.venv_build/bin/activate
pip install pip setuptools --upgrade
pip install wheel
echo "Done!"
echo

echo "##################################################"
echo "#"
echo "# setup python virtual environment for unit test"
echo "#"
echo "##################################################"

rm -rf mkdir ${PROJECT_ROOT}/.venv_test
mkdir ${PROJECT_ROOT}/.venv_test
python3 -m venv ${PROJECT_ROOT}/.venv_test
. ${PROJECT_ROOT}/.venv_test/bin/activate
pip install pip setuptools --upgrade
pip install wheel
pip install -r ${PROJECT_ROOT}/test_requirements.txt
pip install -e ${PROJECT_ROOT}
echo "Done!"
echo

echo "All done!"

