# create test environment
```bash
cd test
mkdir .testenv
python3 -m venv .testenv
source .testenv/bin/activate
pip install pip setuptools --upgrade
pip install wheel
pip install -r requirements.txt
# install dc-client
pip install -e ../
```

# run tests
```bash
cd test
source .testenv/bin/activate
pytest
```
