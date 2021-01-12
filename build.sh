#!/bin/sh

rm -rf build dist src/mordor2.egg-info
python setup.py sdist bdist_wheel --universal
