# Preparation
* You MUST have a linux or compatible machine with Python 3.6 or above installed
* You MUST set environment variable `PROJECT_ROOT` to the root of this repo before running any command in bin directory.

Example:
```bash
export PROJECT_ROOT=$HOME/DATA_DISK/projects/mordor
# consider to put it in ~/.bashrc so you do not need to set it every time manually
```

After you have `PROJECT_ROOT` environment variable set, you need to setup some python virtual environments, to do this, run `bin/setup_env.sh`:

Example:
```bash
bin/setup_env.sh
```

# Various commands:

## To run the unit test
```bash
bin/run_tests.sh
```

## To build the package
```bash
bin/build.sh
```

## To generate python doc
```bash
bin/generate_docs.sh
```


It is recommended to
* run unit test everytime you update the code
* generate pydoc everytime you change API

The docs can be visited at [here](https://stonezhong.github.io/mordor/)
