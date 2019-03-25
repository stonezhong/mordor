import os
from setuptools import setup

# The directory containing this file
HERE = os.path.dirname(os.path.abspath(__file__))

# The text of the README file
with open(os.path.join(HERE, "README.md"), "r") as f:
    README = f.read()

# This call to setup() does all the work
setup(
    name="mordor2",
    version="0.0.18",
    description="Python Deployment Tool",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/stonezhong/mordor",
    author="Stone Zhong",
    author_email="stonezhong@hotmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    packages=["mordor"],
    package_data={"mordor": ["bin/*"]},
    include_package_data=True,
    install_requires=[],
    entry_points={
        "console_scripts": [
            "mordor=mordor.mordor:main",
        ]
    },
)


