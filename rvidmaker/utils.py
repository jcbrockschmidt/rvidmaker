import os
from rake_nltk import Rake
import random
import re

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

def shorten_title(title, max_title_len, alphanum_only=True):
    """
    Shortens a title using important phrases and keywords in the title.

    Args:
        title (str): Title to shorten.
        max_title_len (int): Maximum length of the final title.
        alphanum_only (bool): Whether to only use alphanumeric characters.

    Returns:
        str: Shortened, all lower-case title with a length less than `max_title_len`.
    """
    title = title.lower()
    if alphanum_only:
        filter = re.compile('[^a-z0-9 ]')
        title = filter.sub('', title)

    if len(title) <= max_title_len:
        # Title is already short enough.
        return title

    # Try using the highest ranked phrase from the title.
    r = Rake()
    r.extract_keywords_from_text(title)
    new_title = r.get_ranked_phrases()[0]
    if len(new_title) <= max_title_len:
        return new_title

    # Title is still too long. Use as many of the important words as will fit within the max
    # title length.
    words = sorted(r.get_word_degrees())
    new_title = words[0]
    if len(new_title) > max_title_len:
        # Cut the single-word title short.
        return new_title[:max_title_len]

    for w in words[1:]:
        append_title = '{} {}'.format(new_title, w)
        if len(append_title) > max_title_len:
            break
        new_title = append_title

    return new_title
