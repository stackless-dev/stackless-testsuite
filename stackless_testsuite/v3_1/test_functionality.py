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
import sys
import thread
import threading
import subprocess
from stackless_testsuite.util import StacklessTestCase

if __name__ == '__main__':
    import stackless_testsuite.v3_1  # @NoMove @UnusedImport
    __package__ = "stackless_testsuite.v3_1"  # @ReservedAssignment

if hasattr(threading, "main_thread"):
    # Python 3.4 and later
    def main_thread_id():
        return threading.main_thread().ident  # @UndefinedVariable
else:
    def main_thread_id():
        return threading._shutdown.__self__.ident  # @UndefinedVariable


class AtomicTest(StacklessTestCase):
    """Test the atomic context manager
    """

    def testAtomicCtxt(self):
        old = stackless.getcurrent().atomic
        stackless.getcurrent().set_atomic(False)
        try:
            with stackless.atomic():
                self.assertTrue(stackless.getcurrent().atomic)
        finally:
            stackless.getcurrent().set_atomic(old)

    def testAtomicNopCtxt(self):
        old = stackless.getcurrent().atomic
        stackless.getcurrent().set_atomic(True)
        try:
            with stackless.atomic():
                self.assertTrue(stackless.getcurrent().atomic)
        finally:
            stackless.getcurrent().set_atomic(old)


class OtherTestCases(StacklessTestCase):
    """Test various functions and computed attributes of the module stackless"""

    def testStackless(self):
        # test for the reference to itself
        self.assertIs(stackless, stackless.stackless)

    def testMain(self):
        """test stackless.main"""
        main1 = stackless.main  # @UndefinedVariable
        main2 = stackless.getmain()
        self.assertIs(main1, main2)
        self.assertIsInstance(main1, stackless.tasklet)

    def testCurrent(self):
        """test stackless.current - part 1"""
        current1 = stackless.current  # @UndefinedVariable
        current2 = stackless.getcurrent()
        self.assertIs(current1, current2)
        self.assertIsInstance(current1, stackless.tasklet)

    def testCurrent2(self):
        """test stackless.current - part 2"""
        current = []

        def f():
            current.append(stackless.current)  # @UndefinedVariable

        task = stackless.tasklet().bind(f, ())
        task.run()
        self.assertIs(current[0], task)
        self.assertIsNot(task, stackless.current)  # @UndefinedVariable

    def testMainIsCurrentInThread(self):
        """test, that stackless.main is stackless.current in a new thread"""
        def f():
            self.assertIs(stackless.main, stackless.current)  # @UndefinedVariable
        t = threading.Thread(target=f)
        t.start()
        t.join()

    def testMainIsCurrentInMainThread(self):
        """test, that stackless.main is stackless.current in a new interpreter process"""
        output = subprocess.check_output([sys.executable, "-E", "-c", "import stackless; print(stackless.main is stackless.current)"])
        self.assertEqual(output[:4], b"True")

    def testRuncount(self):
        """Test stackless.runcount. It is a per thread value"""
        rc1 = stackless.runcount  # @UndefinedVariable
        rc2 = stackless.getruncount()
        self.assertIsInstance(rc1, int)
        self.assertIsInstance(rc2, int)
        self.assertEqual(rc1, rc2)
        self.assertGreaterEqual(rc1, 1)

        c = []

        def f():
            c.append(stackless.runcount)  # @UndefinedVariable
            c.append(stackless.getruncount())

        tlet = stackless.tasklet(f)()

        # runcount is now at least 2
        self.assertEqual(stackless.runcount, rc1 + 1)  # @UndefinedVariable
        self.assertEqual(stackless.getruncount(), rc1 + 1)

        t = threading.Thread(target=f)
        t.start()
        t.join()

        self.assertListEqual(c, [1, 1])

        tlet.run()

        self.assertListEqual(c, [1, 1, rc1 + 1, rc1 + 1])
        self.assertEqual(stackless.runcount, rc1)  # @UndefinedVariable
        self.assertEqual(stackless.getruncount(), rc1)


class GetThreadInfoTest(StacklessTestCase):

    def testWithTasklets(self):
        threadid = thread.get_ident()
        info = []

        def f():
            info.extend(stackless.get_thread_info(threadid))

        task = stackless.tasklet().bind(f, ())
        task.run()
        self.assertIs(info[0], stackless.main)  # @UndefinedVariable
        self.assertIs(info[1], task)
        self.assertEqual(info[2], 2)

    def testAllThreads(self):
        for threadid in sys._current_frames():
            info = stackless.get_thread_info(threadid)
            self.assertIsInstance(info, tuple)
            self.assertEqual(len(info), 3)
            self.assertIsInstance(info[0], stackless.tasklet)
            self.assertIs(info[0], info[1])
            self.assertEqual(info[2], 1)

    def testThreads_main(self):
        mti = main_thread_id()
        st = stackless.threads  # @UndefinedVariable
        self.assertIsInstance(st, list)
        # must contain at least the main thread id at index 0
        self.assertGreaterEqual(len(st), 1)
        self.assertEqual(st[0], mti)
        self.assertSetEqual(
            frozenset(st), frozenset(sys._current_frames().keys()))


class SchedulerTest(StacklessTestCase):
    def testRun_args(self):
        """Test, that run accepts the correct arguments

        timeout=0, threadblock=False, soft=False, ignore_nesting=False, totaltimeout=False

        Fortunately, we can call stackless.run with an empty queue for this test.
        """
        stackless.run()
        stackless.run(**dict(timeout=0, threadblock=False, soft=False, ignore_nesting=False, totaltimeout=False))
        stackless.run(0, False, False, False, False)
        self.assertRaisesRegexp(TypeError, r"takes at most 5 arguments", stackless.run, 0, False, False, False, False, None)
