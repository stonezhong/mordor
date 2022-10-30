import os
import json
import yaml


def get_json(path: str):
    with open(os.path.expanduser(path), "r") as f:
        return json.load(f)


def get_yaml(path: str):
    with open(os.path.expanduser(path), "r") as f:
        return yaml.safe_load(f)


def get_config(path: str):
    if path.endswith(".json"):
        return get_json(path)
    if path.endswith(".yaml"):
        return get_yaml(path)
    assert False, "Impossible"
