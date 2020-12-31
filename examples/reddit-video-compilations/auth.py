#!/usr/bin/env python3

from rvidmaker.uploaders import YouTubeUploader, AuthException
import sys
from sys import stderr

if __name__ == "__main__":
    uploader = YouTubeUploader()
    try:
        uploader.auth()
    except AuthException as e:
        print("Failed to authenticate: {}".format(e), file=stderr)
        sys.exit(1)
