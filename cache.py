'''
Created on Nov 25, 2015

@author: ionut
'''

import redis
try:
    import cPickle as pickle
except ImportError:
    import pickle
from settings import REDIS


red = redis.StrictRedis(host=REDIS['host'], port=REDIS['port'])


def set_value(key, obj, timeout=REDIS['default_timeout']):
    """
    Set value in Redis cache
    :param key: key to set the value for
    :param obj: value to save in cache
    :param timeout: time limit to wait for
    """
    value = pickle.dumps(obj)
    red.set(key, value, ex=timeout)


def get_value(key):
    """
    Retrieve cache value for specified key
    :param key: key to retrieve the data for
    :return: retrieved data or None
    """
    value = red.get(key)
    if value:
        return pickle.loads(value)

    return None


def del_value(key):
    """
    Remove object from Redis cache
    :param key: key to remove object for
    """
    red.delete(key)
