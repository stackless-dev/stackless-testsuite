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
import types

import stackless

from stackless_testsuite.util import ROUTINE, PROPERTY, create_type_tests_for_class

DECLARED_API = {'alive': (PROPERTY, bool),
                'atomic': (PROPERTY, bool),
                'bind': ROUTINE,
                'bind_thread': ROUTINE,
                'blocked': (PROPERTY, bool),
                'frame': (PROPERTY, types.FrameType),
                # 'ignore_nesting', depends on impl
                'insert': ROUTINE,
                'is_current': (PROPERTY, bool),
                'is_main': (PROPERTY, bool),
                'kill': ROUTINE,
                # 'nesting_level', depends on impl
                'next': (PROPERTY, stackless.tasklet),
                'paused': (PROPERTY, bool),
                'prev': (PROPERTY, stackless.tasklet),
                'raise_exception': ROUTINE,
                # 'recursion_depth', depends on impl
                'remove': ROUTINE,
                'restorable': (PROPERTY, bool),
                'run': ROUTINE,
                'scheduled': (PROPERTY, bool),
                'set_atomic': ROUTINE,
                # 'set_ignore_nesting', depends on impl
                'setup': ROUTINE,
                'switch': ROUTINE,
                'tempval': (PROPERTY, object),
                'thread_id': (PROPERTY, int),
                'throw': ROUTINE,
                }


class TestTaskletContent(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.the_class = stackless.tasklet
        self.the_instance = stackless.current
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
