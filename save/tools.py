import os

def expand_path(path):
    p1 = os.path.expanduser(path)
    p2 = ps.path.expandvars(p1)
    return p2

def get_json(path):
    with open(expand_path(path), "rt") as f:
        return json.load(f)

