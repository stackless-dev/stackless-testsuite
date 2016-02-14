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

import stackless
from stackless_testsuite.util import StacklessTestCase

if __name__ == '__main__':
    import stackless_testsuite.v3_1.channel  # @NoMove @UnusedImport
    __package__ = "stackless_testsuite.v3_1.channel"  # @ReservedAssignment

try:
    xrange  # @UndefinedVariable
except NameError:
    xrange = range
try:
    long  # @UndefinedVariable
except NameError:
    long = int


class ChannelTest(StacklessTestCase):
    """Test class channel
    """

    #
    # Test method signatures
    #
    def testSig_constructor(self):
        # Stackless: __new__ has the signature (cls, *args, **kw), *args and **kw are ignored
        for result in self.checkSignatureArbitraryArgsAndKw(stackless.channel, 0, *range(20)):
            self.assertIsInstance(result, stackless.channel)

    def testSig_send(self):
        # send(value)
        c = stackless.channel()

        def f():
            while True:
                c.receive()
        t = stackless.tasklet(f)()
        self.addCleanup(t.kill)
        for ret in self.checkSignatureNamedArgs(c.send, 1, None, "value", 42):
            self.assertIsNone(ret)

    def testSig_send_exception(self):
        # send_exception(exc, *args)
        # documented: send_exception(exc, *args)
        # implemented: send_exception(*args) with a check for args[0] being an Exception

        c = stackless.channel()

        def f():
            while True:
                try:
                    c.receive()
                except Exception:
                    pass
        t = stackless.tasklet(f)()
        self.addCleanup(t.kill)
        for ret in self.checkSignatureArbitraryArgs(c.send_exception, 1, "exc", RuntimeError, *xrange(20)):
            self.assertIsNone(ret)

    def testSig_send_throw(self):
        # send_throw(exc[, val[, tb]])
        c = stackless.channel()

        def f():
            while True:
                try:
                    c.receive()
                except Exception:
                    pass
        t = stackless.tasklet(f)()
        self.addCleanup(t.kill)

        for ret in self.checkSignatureNamedArgs(c.send_throw, 1, None, "exc", RuntimeError, "val", None, "tb", None):
            self.assertIsNone(ret)

    def testSig_send_sequence(self):
        # send_sequence(seq)
        c = stackless.channel()

        def f():
            while True:
                try:
                    c.receive()
                except Exception:
                    pass
        t = stackless.tasklet(f)()
        self.addCleanup(t.kill)
        for ret in self.checkSignatureNamedArgs(c.send_sequence, 1, None, "seq", range(42)):
            self.assertEqual(42, ret)

    def testSig___iter__(self):
        # __iter__()
        c = stackless.channel()
        self.assertCallableWith0Args(c.__iter__)
        self.assertIs(c, c.__iter__())

    def testSig_next(self):
        # next()
        c = stackless.channel()

        def f():
            c.send_sequence(xrange(2))
            c.send_exception(StopIteration)
        stackless.tasklet(f)()
        # Stackless raises TypeError("expected 0 arguments, got 1")
        if hasattr(iter([]), 'next'):
            n = c.next
        else:
            n = c.__next__
        self.assertCallableWith0Args(n)
        stackless.run()
        self.assertListEqual([0, 1], list(c))

    def testSig_open(self):
        # open()
        c = stackless.channel()
        self.assertCallableWith0Args(c.open)
        self.assertIsNone(c.open())

    def testSig_close(self):
        # close()
        c = stackless.channel()
        self.assertCallableWith0Args(c.close)
        self.assertIsNone(c.close())

    def testAttr_preference(self):
        c = stackless.channel()
        self.assertIsInstance(c.preference, int)
        self.assertEqual(-1, c.preference)
        c.preference = 0
        self.assertEqual(0, c.preference)
        c.preference = 1
        self.assertEqual(1, c.preference)
        c.preference = -1
        self.assertEqual(-1, c.preference)
        c.preference = 2
        self.assertEqual(1, c.preference)
        c.preference = -2
        self.assertEqual(-1, c.preference)
        self.assertRaisesRegexp(TypeError, "must be set to an integer", setattr, c, "preference", 2.5)
        if int is not long:
            self.assertRaisesRegexp(TypeError, "must be set to an integer",
                                    setattr, c, "preference", 9999999999999999999999999999999999999999999)
        c.preference = True
        self.assertEqual(1, c.preference)

    def testAttr_schedule_all(self):
        c = stackless.channel()
        self.assertIsInstance(c.schedule_all, int)
        self.assertEqual(c.schedule_all, 0)
        c.schedule_all = 1
        self.assertEqual(c.schedule_all, 1)
        c.schedule_all = False
        self.assertEqual(c.schedule_all, 0)
        c.schedule_all = -1
        self.assertEqual(c.schedule_all, 1)
        c.schedule_all = False
        self.assertEqual(c.schedule_all, 0)
        c.schedule_all = 2
        self.assertEqual(c.schedule_all, 1)
        c.schedule_all = False
        self.assertEqual(c.schedule_all, 0)
        c.schedule_all = True
        self.assertEqual(c.schedule_all, 1)
        self.assertRaisesRegexp(TypeError, "must be set to a bool or integer", setattr, c, "schedule_all", 2.5)
        if int is not long:
            self.assertRaisesRegexp(TypeError, "preference must be set to a bool or integer",
                                    setattr, c, "schedule_all", 9999999999999999999999999999999999999999999)

    def testAttr_balance(self):
        c = stackless.channel()
        self.assertIsInstance(c.balance, int)
        self.assertEqual(0, c.balance)
        t = stackless.tasklet(c.send)(None)
        stackless.run()
        self.assertEqual(1, c.balance)
        t2 = stackless.tasklet(c.send)(None)
        stackless.run()
        self.assertEqual(2, c.balance)
        t.kill()
        self.assertEqual(1, c.balance)
        t2.kill()
        self.assertEqual(0, c.balance)
        t = stackless.tasklet(c.receive)()
        stackless.run()
        self.assertEqual(-1, c.balance)
        t2 = stackless.tasklet(c.receive)()
        stackless.run()
        self.assertEqual(-2, c.balance)
        t.kill()
        self.assertEqual(-1, c.balance)
        t2.kill()
        self.assertEqual(0, c.balance)

    def testAttr_closing_closed(self):
        c = stackless.channel()
        self.assertIsInstance(c.closing, bool)
        self.assertIsInstance(c.closed, bool)
        self.assertIs(c.closing, False)
        self.assertIs(c.closed, False)
        t = stackless.tasklet(c.send)(None)
        stackless.run()
        self.assertIs(c.closing, False)
        self.assertIs(c.closed, False)
        c.close()
        self.assertIs(c.closing, True)
        self.assertIs(c.closed, False)
        t.kill()
        self.assertIs(c.closing, True)
        self.assertIs(c.closed, True)
        c.open()
        self.assertIs(c.closing, False)
        self.assertIs(c.closed, False)

    def testAttr_queue(self):
        c = stackless.channel()
        self.assertIsNone(c.queue)
        t = stackless.tasklet(c.send)(None)
        stackless.run()
        self.addCleanup(t.kill)
        self.assertIs(t, c.queue)
        t2 = stackless.tasklet(c.send)(None)
        stackless.run()
        self.addCleanup(t2.kill)
        self.assertIs(t, c.queue)
        self.assertIs(t2, t.next)
