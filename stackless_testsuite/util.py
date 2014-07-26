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

"""
Utility functions and classes
"""

from __future__ import absolute_import, print_function, division

import types
import inspect

FUNCTION = object()
ROUTINE = object()
PROPERTY = (types.GetSetDescriptorType, types.MemberDescriptorType, property)


def _testAttributeTypeTemplate(self, getContainer=None, name=None, expected_type=None):
    container = None
    try:
        container = getContainer(self)
        value = getattr(container, name)
    except AttributeError:
        self.fail("'{}' has no member '{}'".format(container, name))
    if expected_type is callable:
        self.assertTrue(callable(value))
    elif expected_type is FUNCTION:
        self.assertTrue(inspect.isfunction(value) or inspect.isbuiltin(value))
    elif expected_type is ROUTINE:
        self.assertTrue(inspect.isroutine(value))
    else:
        self.assertIsInstance(value, expected_type)


def create_type_tests_for_module(ns, module, api_declared, api_additional):
    api = dict(api_declared)
    api.update(api_additional)
    template = _testAttributeTypeTemplate

    def getContainer(self):
        return module

    for name in api:
        expected_type = api[name]
        test_name = "testAttributeType_" + name
        # create a new function with the right name and
        # default arguments
        ns[test_name] = types.FunctionType(template.__code__,
                                           template.__globals__,
                                           test_name,
                                           (getContainer, name, expected_type))


def create_type_tests_for_class(ns, api):
    template = _testAttributeTypeTemplate
    for index, prefix, getContainer in ((0, 'testAttributeTypeOnClass_', lambda self: self.the_class),
                                        (1, 'testAttributeTypeOnInstance_', lambda self: self.the_instance)):
        for name in api:
            expected_type = api[name]
            if isinstance(expected_type, tuple) and len(expected_type) == 2:
                expected_type = expected_type[index]
            test_name = prefix + name
            # create a new function with the right name and
            # default arguments
            ns[test_name] = types.FunctionType(template.__code__,
                                               template.__globals__,
                                               test_name,
                                               (getContainer, name, expected_type))
