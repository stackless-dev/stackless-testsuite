#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 by Anselm Kruis
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from __future__ import absolute_import, print_function, division

from setuptools import setup

# The full version, including alpha/beta/rc tags.
release = '0.0.0'

setup(
    name='stackless_testsuite',
    version=release,
    description='Test-suite for the stackless API',
    author='Anselm Kruis',
    author_email='a.kruis@science-computing.de',
    url='https://bitbucket.org/akruis/stackless-testsuite',
    packages=['stackless_testsuite'],

    # don't forget to add these files to MANIFEST.in too
    # package_data={'pyheapdump': ['examples/*.py']},

    long_description="""
Test-Suit for stackless
-----------------------

There are various implementations of the Python stackless API.

* `Stackless <http://www.stackless.com>`_
* `PyPy <http://pypy.org>`_

This test suite can be used by both projects.
""",
    classifiers=["License :: OSI Approved :: Apache Software License",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: Implementation :: PyPy",
                 "Programming Language :: Python :: Implementation :: Stackless",
                 "Environment :: Console",
                 "Operating System :: OS Independent",
                 "Development Status :: 3 - Alpha",  # hasn't been tested outside of flowGuide2
                 "Intended Audience :: Developers",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 ],
    keywords='stackless',
    license='Apache Software License',
    platforms="any",
    test_suite="stackless_testsuite",
)
