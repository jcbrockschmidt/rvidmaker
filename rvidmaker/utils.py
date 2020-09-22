import os
import random

_CHAR_LIST = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

class DirNotFound(Exception):
    """Raised if a directory does not exist"""

def random_string(n):
    """
    Generates a string of random characters.

    Args:
        n (int): Length of string.

    Returns:
        str: The randomly generated string.
    """
    s = ''.join((random.choice(_CHAR_LIST) for i in range(n)))
    return s

def get_random_path(root, ext):
    """
    Args:
        root (str): Directory to generate path within.
        ext (str): File extension for the random path.

    Returns:
        str: A random, unique path within the provided root directory.

    Raises:
        DirectoryNotFound: If root directory does not exist.
    """
    if not os.path.isdir(root):
        raise DirNotFound
    while True:
        rand_str = random_string(10)
        path = os.path.join(root, '{}.{}'.format(rand_str, ext))
        if not os.path.exists(path):
            return path
