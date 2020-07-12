import random

_CHAR_LIST = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

def random_string(n):
    """
    Generates a string of random characters.

    Args:
        n (int): Length of string.

    Returns:
        (str) The randomly generated string.
    """
    s = ''.join((random.choice(_CHAR_LIST) for i in range(n)))
    return s
