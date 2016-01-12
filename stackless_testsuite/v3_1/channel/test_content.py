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

import unittest

import stackless

from stackless_testsuite.util import ROUTINE, PROPERTY, create_type_tests_for_class

NEXT_NAME = "next" if hasattr(iter(()), "next") else "__next__"

DECLARED_API = {'__iter__': (ROUTINE, callable),
                'balance': (PROPERTY, int),
                'close': ROUTINE,
                'closed': (PROPERTY, bool),
                'closing': (PROPERTY, bool),
                NEXT_NAME: (ROUTINE, callable),
                'open': ROUTINE,
                'preference': (PROPERTY, int),
                'queue': (PROPERTY, (stackless.tasklet, type(None))),
                'receive': ROUTINE,
                'schedule_all': (PROPERTY, int),
                'send': ROUTINE,
                'send_exception': ROUTINE,
                'send_sequence': ROUTINE,
                'send_throw': ROUTINE,
                }


class TestTaskletContent(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.the_class = stackless.channel
        self.the_instance = stackless.channel()
        self.assertIsInstance(self.the_instance, self.the_class)

    def testDeclaredNames(self):
        definedNames = set(dir(self.the_class))
        expectedNames = set(DECLARED_API)
        missing = expectedNames - definedNames
        self.assertFalse(missing, "Missing names {}".format(missing))

    # create the remaining tests dynamically
    create_type_tests_for_class(locals(), DECLARED_API)

if __name__ == "__main__":
    unittest.main()
