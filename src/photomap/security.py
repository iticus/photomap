"""
Created on 2021-12-18

@author: iticus
"""

import logging

from argon2 import PasswordHasher, exceptions

logger = logging.getLogger(__name__)


def make_pw_hash(password: str) -> str:
    """
    Generate argon2id password hash
    :param password: password text to be hashed
    :returns: password hash
    """
    password_hasher = PasswordHasher()
    pw_hash = password_hasher.hash(password)
    return pw_hash


def compare_pwhash(pw_hash: str, password: str) -> bool:
    """
    Compute hash for current password and compare it to pw_hash
    :param pw_hash: previously generated pw_hash to be compared
    :param password: password text to compute hash for
    :returns: True or False
    """
    password_hasher = PasswordHasher()
    try:
        password_hasher.verify(pw_hash, password)
        # check rehash
        # needs_rehash = False
        # if result:
        #     needs_rehash = ph.check_needs_rehash(pw_hash)
    except exceptions.VerifyMismatchError:
        return False
    except exceptions.InvalidHash:
        logger.error("tried to decode invalid hash: %s", password)
        return False
    return True
