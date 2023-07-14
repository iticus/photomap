"""
Created on Nov 25, 2015

@author: ionut
"""

try:
    import cPickle as pickle
except ImportError:
    import pickle


async def set_value(red, key, obj):
    """
    Set value in Redis cache
    :param red: redis instance
    :param key: key to set the value for
    :param obj: value to save in cache
    """
    value = pickle.dumps(obj)
    await red.set(key, value)


async def get_value(red, key):
    """
    Retrieve cache value for specified key
    :param red: redis instance
    :param key: key to retrieve the data for
    :return: retrieved data or None
    """
    value = await red.get(key)
    if value:
        return pickle.loads(value)
    return None


async def del_value(red, key):
    """
    Remove object from Redis cache
    :param red: redis instance
    :param key: key to remove object for
    """
    await red.delete(key)
