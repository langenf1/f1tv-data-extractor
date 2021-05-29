#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os

from setuptools import setup, find_packages

# Package meta-data.
NAME = 'F1RaceSectors'
DESCRIPTION = 'F1RaceSectors - Retrieves F1 Race Sectors from a F1TV Data Channel Recording'
AUTHOR = 'langenf1'
REQUIRES_PYTHON = '>=3.9.0'
VERSION = '0.0.1'

# List of required packages
REQUIRED = [
    'argparse~=1.4.0',
    'opencv-python~=4.5.1.48',
    'tqdm~=4.60.0',
    'numpy~=1.20.2',
    'pytesseract~=0.3.7',
    'Pillow~=8.2.0',
    'matplotlib~=3.4.1',
    'seaborn~=0.11.1',
    'pandas~=1.2.3'
]

# Optional packages
EXTRAS = {
    # None
}

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    python_requires=REQUIRES_PYTHON,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
)
