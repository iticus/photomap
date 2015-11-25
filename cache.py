'''
Created on Nov 25, 2015

@author: ionut
'''

import redis
try:
    import cPickle as pickle
except:
    import pickle
from settings import REDIS

r = redis.StrictRedis(host=REDIS['host'], port=REDIS['port'])

def set_value(key, obj, timeout=REDIS['default_timeout']):
    value = pickle.dumps(obj)
    r.set(key, value, ex=timeout)
    
def get_value(key):
    value = r.get(key)
    if value:
        return pickle.loads(value)

    return None

def del_value(key):
    r.delete(key)