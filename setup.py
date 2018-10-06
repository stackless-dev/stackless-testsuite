#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 by Anselm Kruis
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

from distutils.core import setup

# The full version, including alpha/beta/rc tags.
release = '0.0.1'

setup(
    name='stackless_testsuite',
    version=release,
    description='Test-suite for the stackless API',
    author='Anselm Kruis',
    author_email='anselm.kruis@atos.net',
    url='https://github.com/stackless-dev/stackless-testsuite',
    packages=['stackless_testsuite',
              'stackless_testsuite.v3_1',
              'stackless_testsuite.v3_1.tasklet',
              'stackless_testsuite.v3_1.channel'],

    long_description="""
Test-Suit for Stackless-Python
------------------------------

There are various implementations of the Python Stackless API.

* `Stackless <http://www.stackless.com>`_
* `PyPy <http://pypy.org>`_

This test suite can be used by both projects.

Usage::
   $ python -m unittest discover

""",
    classifiers=["License :: OSI Approved :: Apache Software License",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: Implementation :: PyPy",
                 "Programming Language :: Python :: Implementation :: Stackless",
                 "Environment :: Console",
                 "Operating System :: OS Independent",
                 "Development Status :: 3 - Alpha",
                 "Intended Audience :: Developers",
                 "Topic :: Software Development :: Libraries :: Python Modules",
                 ],
    keywords='stackless',
    license='Apache Software License',
    platforms="any",
)
