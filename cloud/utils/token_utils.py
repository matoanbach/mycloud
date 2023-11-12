import jwt
from cloud.utils.env_key_getter import get_key
import environ
import os
env = environ.Env()
environ.Env.read_env()

jwt_key = get_key('JWT_SECRET')
expires_in = get_key('JWT_EXPIRES_IN')

def create_jwt(payload):
    token = jwt.encode(payload, jwt_key, algorithm="HS256")
    return token

def verify_jwt(token):
    decoded = jwt.decode(token, jwt_key, algorithms="HS256")
    return decoded