# Step 1: Test ssh
make sure you can ssh to localhost, try `ssh localhost` in terminal

# Step 2: checkout sample, initialize target host for mordor
```bash
mkdir ~/mordortest
cd ~/mordortest/

# first, let create a virtual environment
mkdir .venv
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pip setuptools --upgrade
python3 -m pip install mordor2

# now checkout the example
git clone https://github.com/stonezhong/mordor.git

cd mordor

# now initialize the target host
mordor init-host -c samples/simple/config -o localhost
```

# Step 3: stage application "sample"
```bash
mordor stage -c samples/simple/config -p sample -s beta --update-venv
```

# Step 4: run the application on target
```bash
ssh localhost
eae sample
./main.py
```
