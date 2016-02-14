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
import re
import stackless

FUNCTION = object()
ROUTINE = object()
PROPERTY = (types.GetSetDescriptorType, types.MemberDescriptorType, property)

try:
    long
except NameError:
    long = int


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


def require_one_thread(testcase):
    if withThreads:
        return unittest.skipIf(threading.active_count() > 1, "Test requires, that only a single thread is active")(testcase)
    return testcase


class StacklessTestCaseMixin(object):
    def skipUnlessSoftswitching(self):
        try:
            enable_softswitch = stackless.enable_softswitch
        except AttributeError:
            def enable_softswitch(x):
                return False
        if not enable_softswitch(None):
            self.skipTest("test requires softswitching")

    def assertCallableWith0Args(self, func, additionalArg=None):
        self.assertRaisesRegexp(TypeError, r"takes no arguments|expected 0 arguments", func, additionalArg)

    _NO_KWARGS_RE = r"takes no keyword arguments"
    _NO_KWARGS_RE = re.compile(_NO_KWARGS_RE)

    def checkSignatureArbitraryArgsAndKw(self, func, nb_mandatory, *namesAndArgs):
        for r in self._checkSignature(func, nb_mandatory, "both", None, *namesAndArgs):
            yield r

    def checkSignatureArbitraryArgs(self, func, nb_mandatory, *namesAndArgs):
        for r in self._checkSignature(func, nb_mandatory, "args", None, *namesAndArgs):
            yield r

    def checkSignatureArbitraryKw(self, func, nb_mandatory, *namesAndArgs):
        for r in self._checkSignature(func, nb_mandatory, "kw", None, *namesAndArgs):
            yield r

    def checkSignatureNamedArgs(self, func, nb_mandatory, additionalArg, *namesAndArgs):
        for r in self._checkSignature(func, nb_mandatory, False, additionalArg, *namesAndArgs):
            yield r

    def _checkSignature(self, func, nb_mandatory, accept_arbitrary, additionalArg, *namesAndArgs):
        # check arguments and build the argument list
        self.assertIsInstance(nb_mandatory, int)
        self.assertGreaterEqual(nb_mandatory, 0)
        self.assertGreaterEqual(len(namesAndArgs) / 2, nb_mandatory)
        if not accept_arbitrary:
            self.assertGreaterEqual(len(namesAndArgs), 2)
            self.assertTrue(len(namesAndArgs) % 2 == 0)
            namesAndArgs_iter = iter(namesAndArgs)
        else:
            namesAndArgs_iter = iter(namesAndArgs[:nb_mandatory * 2])
        args = []
        names = []
        kwargs = {}
        for n in namesAndArgs_iter:
            v = (getattr(namesAndArgs_iter, "next", None) or namesAndArgs_iter.__next__)()
            self.assertIsInstance(n, str)
            args.append(v)
            names.append(n)
            kwargs[n] = v
        if accept_arbitrary:
            for i, v in enumerate(namesAndArgs[nb_mandatory * 2:]):
                n = "_arbitrary_nonsens_arg{0}_".format(i)
                args.append(v)
                names.append(n)
                kwargs[n] = v

        # try a call with args and additional arg
        exc_msg = r"(takes|expected) at most {0} argument".format(len(args))
        if len(args) == nb_mandatory:
            if nb_mandatory == 1:
                exc_msg = r"takes exactly one argument"
            else:
                pass
        if not accept_arbitrary:
            self.assertRaisesRegexp(TypeError, exc_msg,
                                    func, *(args + [additionalArg]))
        if nb_mandatory > 0:
            exc_msg = r"(takes|expected) at least {0} argument|Required argument '{1}' \(pos 1\) not found".format(nb_mandatory, names[0])
            if len(args) == nb_mandatory:
                if nb_mandatory == 1:
                    exc_msg = r"takes exactly one argument"
                else:
                    pass
            self.assertRaisesRegexp(TypeError, exc_msg, func)
        # only required positional arguments
        yield func(*(args[:nb_mandatory]))
        # all positional arguments
        if accept_arbitrary != "kw":
            yield func(*args)
        # try a call with kwargs
        try:
            # all arguments as kwargs
            if accept_arbitrary != "args":
                yield func(**kwargs)
            else:
                # only required args as kw-args
                yield func(**dict((k, kwargs[k]) for k in names[:nb_mandatory]))
                return
        except TypeError as e:
            if not self._NO_KWARGS_RE.search(str(e)):
                raise
            return
        else:
            # only required args as kw-args
            yield func(**dict((k, kwargs[k]) for k in names[:nb_mandatory]))


class StacklessTestCase(unittest.TestCase, StacklessTestCaseMixin):
    __preexisting_threads = None

    def setUp_thread_counter(self):
        if withThreads and self.__preexisting_threads is None:
            self.__preexisting_threads = frozenset(threading.enumerate())
            return len(self.__preexisting_threads)
        return 1

    def setUp(self):
        self.assertEqual(stackless.getruncount(), 1, "Leakage from other tests, with %d tasklets still in the scheduler" % (stackless.getruncount() - 1))
        expected_thread_count = self.setUp_thread_counter()
        if withThreads:
            active_count = threading.active_count()
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
        run_count = stackless.getruncount()
        self.assertEqual(run_count, 1, "Leakage from this test, with %d tasklets still in the scheduler" % (run_count - 1))
        if withThreads:
            preexisting_threads = self.__preexisting_threads
            self.__preexisting_threads = None  # avoid pickling problems, see _addSkip
            expected_thread_count = len(preexisting_threads)
            active_count = threading.active_count()
            if active_count > expected_thread_count:
                activeThreads = set(threading.enumerate())
                activeThreads -= preexisting_threads
                self.assertNotIn(threading.current_thread(), activeThreads, "tearDown runs on the wrong thread.")
                while activeThreads:
                    activeThreads.pop().join(0.5)
                active_count = threading.active_count()
            self.assertEqual(active_count, expected_thread_count, "Leakage from other threads, with %d threads running (%d expected)" % (active_count, expected_thread_count))

    def _addSkip(self, result, reason):
        # Remove non standard attributes. They could render the test case object unpickleable.
        # This is a hack, but it works fairly well.
        for k in list(self.__dict__.keys()):
            if k not in self.SAFE_TESTCASE_ATTRIBUTES and \
                    not isinstance(self.__dict__[k], (type(None), type(u""), type(b""), int, long, float)):
                del self.__dict__[k]
        super(StacklessTestCase, self)._addSkip(result, reason)

_tc = StacklessTestCase(methodName='run')
try:
    _tc.setUp()
    StacklessTestCase.SAFE_TESTCASE_ATTRIBUTES = _tc.__dict__.keys()
finally:
    del _tc


class AsTaskletTestCase(StacklessTestCase):
    """A test case class, that runs tests as tasklets"""

    def setUp(self):
        self._ran_AsTaskletTestCase_setUp = True
        if stackless.enable_softswitch(None):
            self.assertEqual(stackless.current.nesting_level, 0)

        # yes, its intended: call setUp on the grand parent class
        super(StacklessTestCase, self).setUp()
        expected_thread_count = self.setUp_thread_counter()
        self.assertEqual(stackless.getruncount(
        ), 1, "Leakage from other tests, with %d tasklets still in the scheduler" % (stackless.getruncount() - 1))
        if withThreads:
            active_count = threading.active_count()
            self.assertEqual(active_count, expected_thread_count, "Leakage from other threads, with %d threads running (%d expected)" % (active_count, expected_thread_count))

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
