#!/usr/bin/env python3

from rvidmaker.uploaders import YouTubeUploader

if __name__ == "__main__":
    uploader = YouTubeUploader()
    uploader.auth()
