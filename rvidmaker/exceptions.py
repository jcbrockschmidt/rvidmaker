"""Defines custom exceptions for all submodules"""

class ConfigNotFound(Exception):
    """Raised when no config file is found"""

class RedditApiException(Exception):
    """Raised when no config file is found"""
    def __init__(self, msg):
        super().__init__(msg)
