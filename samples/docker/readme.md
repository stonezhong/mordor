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
mordor init-host -c samples/docker/config -o localhost
```

# Step 3: stage application "sample"
```bash
mordor stage -c samples/docker/config -p sample -s beta --update-venv
```

# Step 4: run the application on target
```bash
ssh localhost
cd $ENV_HOME/data/sample/docker
docker compose up
```
Then try to open a browser and type `http://localhost:8000/`, you will see `Hello World! I have been seen 1 times.`

You can press CTRL-C to stop all services, next time, you can do `docker compose up -d` to start these services as daemon.
