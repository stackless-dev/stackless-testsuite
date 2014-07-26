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
import __builtin__

from stackless_testsuite import stackless_api
from stackless_testsuite.util import FUNCTION, create_type_tests_for_module
import stackless

# you get them by "from stackless import *"
DECLARED_API = {# 'bomb': callable,  # undocumented in the manual
                'atomic': type,
                # 'set_error_handler': callable,  # undocumented in the manual, debug related
                'getmain': FUNCTION,
                # 'switch_trap': FUNCTION, debug related
                'get_thread_info': FUNCTION,
                'tasklet': type,
                'stackless': types.ModuleType,
                'run': FUNCTION,
                'schedule': FUNCTION,
                'getruncount': FUNCTION,
                'schedule_remove': FUNCTION,
                'getcurrent': FUNCTION,
                # 'enable_softswitch': FUNCTION,  depends on the implementation
                'getcurrentid': FUNCTION,  # undocumented in the manual
                'channel': type,
                }

# not imported by a "from stackless import *", but provided and documented
ADDITIONAL_API = {"current": stackless.tasklet,
                  "main": stackless.tasklet,
                  "runcount": int,
                  "threads": list,
                  }


class TestModuleContent(unittest.TestCase):

    def testDeclaredNames(self):
        definedNames = set(stackless_api.__dict__)
        expectedNames = set(DECLARED_API)
        missing = expectedNames - definedNames
        self.assertFalse(missing, "Missing names {}".format(missing))

    def testAdditionalNames(self):
        missing = set()
        for name in ADDITIONAL_API:
            try:
                getattr(stackless, name)
            except AttributeError:
                missing.add(name)
        self.assertFalse(missing, "Missing names {}".format(missing))

    def testTaskletExit(self):
        # TaskletExit is special, as it is defined in __builtin__
        try:
            te = __builtin__.TaskletExit
        except AttributeError:
            self.fail("__builtin__ does not contain TaskletExit")
        # Stackless Documentation says so
        self.assertTrue(issubclass(te, SystemExit), "TaskletExit is not a subclass of SystemExit")

    #  create the remaining tests dynamically
    create_type_tests_for_module(locals(), stackless, DECLARED_API, ADDITIONAL_API)


if __name__ == "__main__":
    unittest.main()
