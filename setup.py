#!/usr/bin/env python3

import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="rvidmaker",
    version="0.0.1",
    description="Automatically generates narrated videos of Reddit articles",
    author="Jaclyn Brockschmidt",
    author_email="jcbrockschmidt@gmail.com",
    url="https://github.com/jcbrockschmidt/rvidmaker",
    install_requires=[
        "apiclient==1.0.4",
        "better-profanity>=0.6.1",
        "ffmpeg-python>=0.2.0",
        "google-api-python-client>=1.12.8",
        "gtts>=2.1.1",
        "httplib2==0.18.1",
        "moviepy>=1.0.3",
        "nltk>=3.5",
        "oauth2client==4.1.3",
        "Pillow>=7.2.0",
        "praw>=7.1.4",
        "rake-nltk>=1.0.4",
        "textblob>=0.15.3",
        "toml>=0.10.2",
    ],
    packages=[
        "rvidmaker",
        "rvidmaker.editor",
        "rvidmaker.readers",
        "rvidmaker.suites",
        "rvidmaker.thumbnails",
        "rvidmaker.uploaders",
        "rvidmaker.videos",
        "rvidmaker.voices",
    ],
)
