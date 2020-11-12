from bisect import insort
import os
from rake_nltk import Rake
import random
import re

_CHAR_LIST = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


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
    s = "".join((random.choice(_CHAR_LIST) for i in range(n)))
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
        path = os.path.join(root, "{}.{}".format(rand_str, ext))
        if not os.path.exists(path):
            return path


def shorten_title(title, max_title_len, alpha_only=True):
    """
    Shortens a title using important phrases and keywords in the title.

    Args:
        title (str): Title to shorten.
        max_title_len (int): Maximum length of the final title.
        alpha_only (bool): Whether to only use alphabetic characters.

    Returns:
        str: Shortened, all lower-case title with a length less than `max_title_len`.
    """
    title = title.lower()
    if len(title) <= max_title_len:
        # Title is already short enough.
        return title

    if alpha_only:
        filter = re.compile("[^a-z ]")
        title = filter.sub("", title)

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
        append_title = "{} {}".format(new_title, w)
        if len(append_title) > max_title_len:
            break
        new_title = append_title

    return new_title


def extract_tags(
    videos, blocklist=None, max_tag_len=0, max_total_chars=0, max_total_tags=0
):
    """
    Creates tags from a list of videos.

    Args:
        videos (list): List videos as `rvidmaker.videos.VideoRef`s. Tags are extracted from
            their titles.
        blocklist (better_profanity.Profanity): Filters out tags with undesirable words or phrases.
            `None` to not perform any filtering.
        max_tag_len (int): Maximum character length of a tag. 0 for no maximum length.
        max_total_chars (int): Maximum total number of characters. 0 for no limit.
        max_total_tags (int): Maximum total character length. 0 for no limit.
    """
    ranked_tags = []
    filter = re.compile("[^a-z ]")
    r = Rake()
    for v in videos:
        title = filter.sub("", v.get_title().lower())
        r.extract_keywords_from_text(title)
        phrases = r.get_ranked_phrases_with_scores()
        for score, phrase in phrases:
            if score <= 1:
                continue
            if max_tag_len > 0 and len(phrase) > max_tag_len:
                continue
            if blocklist is not None:
                if blocklist.contains_profanity(phrase):
                    continue
            insort(ranked_tags, (score, phrase))
    tags = set()
    total_chars = 0
    for _, tag in reversed(ranked_tags):
        if max_total_chars > 0:
            total_chars += len(tag)
            if total_chars >= max_total_chars:
                break
        tags.add(tag)
        if max_total_tags > 0 and len(tags) >= max_total_tags:
            break
    return tags
