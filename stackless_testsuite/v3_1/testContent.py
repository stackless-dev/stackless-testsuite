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
import inspect

from stackless_testsuite import stackless_api
import stackless

FUNCTION = object()

DECLARED_API = {'bomb': callable,  # undocumented in the manual
                'atomic': type,
                'set_error_handler': callable,  # undocumented in the manual
                'getmain': FUNCTION,
                'switch_trap': FUNCTION,
                'get_thread_info': FUNCTION,
                'tasklet': type,
                'stackless': types.ModuleType,
                'run': FUNCTION,
                'schedule': FUNCTION,
                'getruncount': FUNCTION,
                'schedule_remove': FUNCTION,
                'getcurrent': FUNCTION,
                'enable_softswitch': FUNCTION,
                'getcurrentid': FUNCTION,  # undocumented in the manual
                'channel': type,
                }
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

    # create the remaining tests dynamically
    def typeTest(self, name=None, expected_type=None):
        try:
            value = getattr(stackless, name)
        except AttributeError:
            self.fail("API name {} not defined".format(name))
        if expected_type is callable:
            self.assertTrue(callable(value))
        elif expected_type is FUNCTION:
            self.assertTrue(inspect.isfunction(value) or inspect.isbuiltin(value))
        else:
            self.assertIsInstance(value, expected_type)

    api = dict(DECLARED_API)
    api.update(ADDITIONAL_API)
    ns = locals()
    for name in api:
        test_name = "testTypeOf_" + name
        # create a new function with the right name and
        # default arguments
        ns[test_name] = types.FunctionType(typeTest.__code__,
                                           typeTest.__globals__,
                                           test_name,
                                           (name, api[name]))
    del typeTest


if __name__ == "__main__":
    unittest.main()
