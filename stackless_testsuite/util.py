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
import sys
import unittest
import stackless

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


try:
    import threading
    withThreads = True
except:
    withThreads = False


class StacklessTestCase(unittest.TestCase):
    __preexisting_threads = None

    def setUp(self):
        self.assertEqual(stackless.getruncount(), 1, "Leakage from other tests, with %d tasklets still in the scheduler" % (stackless.getruncount() - 1))
        if withThreads:
            active_count = threading.active_count()
            if self.__preexisting_threads is None:
                self.__preexisting_threads = frozenset(threading.enumerate())
            expected_thread_count = len(self.__preexisting_threads)
            self.assertEqual(active_count, expected_thread_count, "Leakage from other threads, with %d threads running (%d expected)" % (active_count, expected_thread_count))

    def tearDown(self):
        # Tasklets created in pickling tests can be left in the scheduler when they finish.  We can feel free to
        # clean them up for the tests.  Any tests that expect to exit with no leaked tasklets should do explicit
        # assertions to check.
        mainTasklet = stackless.getmain()
        current = mainTasklet.next
        while current is not None and current is not mainTasklet:
            next_ = current.next
            current.kill()
            current = next_
        self.assertEqual(stackless.getruncount(
        ), 1, "Leakage from this test, with %d tasklets still in the scheduler" % (stackless.getruncount() - 1))
        if withThreads:
            expected_thread_count = len(self.__preexisting_threads)
            active_count = threading.active_count()
            if active_count > expected_thread_count:
                activeThreads = set(threading.enumerate())
                activeThreads -= self.__preexisting_threads
                self.assertNotIn(threading.current_thread(), activeThreads, "tearDown runs on the wrong thread.")
                while activeThreads:
                    activeThreads.pop().join(0.5)
                active_count = threading.active_count()
            self.assertEqual(active_count, expected_thread_count, "Leakage from other threads, with %d threads running (%d expected)" % (active_count, expected_thread_count))

    SAFE_TESTCASE_ATTRIBUTES = unittest.TestCase(
        methodName='run').__dict__.keys()

    def _addSkip(self, result, reason):
        # Remove non standard attributes. They could render the test case object unpickleable.
        # This is a hack, but it works fairly well.
        for k in self.__dict__.keys():
            if k not in self.SAFE_TESTCASE_ATTRIBUTES and \
                    not isinstance(self.__dict__[k], (types.NoneType, basestring, int, long, float)):
                del self.__dict__[k]
        super(StacklessTestCase, self)._addSkip(result, reason)


class AsTaskletTestCase(StacklessTestCase):
    """A test case class, that runs tests as tasklets"""

    def setUp(self):
        self._ran_AsTaskletTestCase_setUp = True
        if stackless.enable_softswitch(None):
            self.assertEqual(stackless.current.nesting_level, 0)  # @UndefinedVariable

        # yes, its intended: call setUp on the grand parent class
        super(StacklessTestCase, self).setUp()
        self.assertEqual(stackless.getruncount(
        ), 1, "Leakage from other tests, with %d tasklets still in the scheduler" % (stackless.getruncount() - 1))
        if withThreads:
            self.assertEqual(threading.activeCount(
            ), 1, "Leakage from other threads, with %d threads running (1 expected)" % (threading.activeCount()))

    def run(self, result=None):
        c = stackless.channel()
        c.preference = 1  # sender priority
        self._ran_AsTaskletTestCase_setUp = False

        def helper():
            try:
                c.send(super(AsTaskletTestCase, self).run(result))
            except:
                c.send_throw(*sys.exc_info())
        stackless.tasklet(helper)()
        result = c.receive()
        assert self._ran_AsTaskletTestCase_setUp
        return result
