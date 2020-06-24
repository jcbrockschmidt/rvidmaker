#!/usr/bin/env python3

import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# Get dependencies from requirements.txt
dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, 'requirements.txt')) as f:
    requires = f.read().splitlines()

setup(
    name = 'rvidmaker',
    version = '0.0.1',
    description = 'Automatically generates narrated videos of Reddit articles',
    author = 'Jaclyn Brockschmidt',
    author_email = 'jcbrockschmidt@gmail.com',
    url = 'https://github.com/jcbrockschmidt/rvidmaker',
    install_requires = requires
)
