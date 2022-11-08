import os
from setuptools import setup, find_packages

# The directory containing this file
HERE = os.path.dirname(os.path.abspath(__file__))

# The text of the README file
with open(os.path.join(HERE, "README.md"), "r") as f:
    README = f.read()

# This call to setup() does all the work
setup(
    name="mordor2",
    version="0.0.57",
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
    package_dir = {'': 'src'},
    packages=find_packages(where='src'),
    package_data={"mordor": ["bin/*"]},
    include_package_data=True,
    install_requires=["PyYAML", "Jinja2"],
    entry_points={
        "console_scripts": [
            "mordor=mordor.mordor:main",
        ]
    },
)


