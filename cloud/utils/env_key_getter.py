import os
import environ
env = environ.Env()
environ.Env.read_env()


def get_key(key):
    _key = os.environ.get(key)
    return _key