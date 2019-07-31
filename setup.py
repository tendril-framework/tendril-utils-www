#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
    from setuptools import find_packages
except ImportError:
    from distutils.core import setup
    find_packages = None


with open('README.rst') as readme_file:
    readme = readme_file.read()

import sys
if sys.version_info > (3, 0):
    suds = 'suds-py3'
else:
    suds = 'suds'


requirements = [
    'tendril-utils-core>=0.1.12',
    'tendril-config>=0.1.6',
    'six',
    'lxml',
    'beautifulsoup4',
    'cachecontrol[filecache]',
    'requests',
    suds,
    'fs==0.5.4',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='tendril-utils-www',
    version='0.1.6',
    description="Internet utilities for tendril",
    long_description=readme,
    author="Chintalagiri Shashank",
    author_email='shashank@chintal.in',
    url='https://github.com/chintal/tendril-utils-www',
    packages=find_packages(),
    install_requires=requirements,
    license="AGPLv3",
    zip_safe=False,
    keywords='tendril',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Programming Language :: Python',
    ],
    # test_suite='tests',
    # tests_require=test_requirements
)
