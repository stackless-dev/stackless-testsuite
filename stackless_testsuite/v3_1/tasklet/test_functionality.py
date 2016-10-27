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
import threading
from stackless_testsuite.util import StacklessTestCase

if __name__ == '__main__':
    import stackless_testsuite.v3_1.tasklet  # @NoMove @UnusedImport
    __package__ = "stackless_testsuite.v3_1.tasklet"  # @ReservedAssignment

try:
    xrange
except NameError:
    xrange = range  # @ReservedAssignment


if hasattr(threading, "main_thread"):
    # Python 3.4 and later
    def main_thread_id():
        return threading.main_thread().ident  # @UndefinedVariable
else:
    def main_thread_id():
        return threading._shutdown.__self__.ident  # @UndefinedVariable


def nop(*args, **kw):
    pass


class TestError(Exception):
    pass


class TaskletTest(StacklessTestCase):
    """Test class tasklet
    """

    #
    # Test method signatures
    #
    def testSig_constructor(self):
        # tasklet(func=None, args=None, kwargs=None)
        for ret in self.checkSignatureNamedArgs(stackless.tasklet, 0, None, "func", None, "args", None, "kwargs", None):
            self.assertIsInstance(ret, stackless.tasklet)

    def testSig_bind(self):
        # tasklet.bind(func=None, args=None, kwargs=None)
        t = stackless.tasklet()
        for ret in self.checkSignatureNamedArgs(t.bind, 0, None, "func", nop, "args", (), "kwargs", {}):
            self.assertIsInstance(ret, stackless.tasklet)

    def testSig_setup(self):
        # setup(*args, **kw)
        t = stackless.tasklet(nop)
        self.addCleanup(t.kill)
        for res in self.checkSignatureArbitraryArgsAndKw(t.setup, 0, *range(20)):
            self.assertIsInstance(res, stackless.tasklet)
            t.remove().bind(nop)

    def testSig___call__(self):
        # __call__(*args, **kw)
        t = stackless.tasklet(nop)
        self.addCleanup(t.kill)
        for res in self.checkSignatureArbitraryArgsAndKw(t, 0, *range(20)):
            self.assertIsInstance(res, stackless.tasklet)
            t.remove().bind(nop)

    def testSig_insert(self):
        t = stackless.tasklet(nop, ())
        self.assertCallableWith0Args(t.insert)
        self.assertIs(t, t.insert())
        t.kill()

    def testSig_remove(self):
        t = stackless.tasklet(nop)()
        self.assertCallableWith0Args(t.remove)
        self.assertIs(t, t.remove())
        t.kill()

    def testSig_run(self):
        t = stackless.tasklet(nop)()
        self.assertCallableWith0Args(t.run)
        o = object()
        stackless.current.tempval = o
        self.assertIs(o, t.run())

    def testSig_switch(self):
        t = stackless.tasklet(nop)()
        self.assertCallableWith0Args(t.switch)
        o = object()
        stackless.current.tempval = o
        self.assertIs(o, t.switch())

    def testSig_raise_exception(self):
        # documented: raise_exception(exc_class, *args)
        # implemented: raise_exception(*args) with a check for args[0] being an Exception
        done = []

        def f():
            while True:
                try:
                    stackless.schedule_remove()
                except TestError:
                    done.append(True)
        t = stackless.tasklet(f)()
        stackless.run()
        self.addCleanup(t.kill)
        for ret in self.checkSignatureArbitraryArgs(t.raise_exception, 1, "exc_class", TestError, *xrange(20)):
            self.assertIsNone(ret)
        self.assertTrue(done)

    def testSig_throw(self):
        # throw(exc=None, val=None, tb=None, pending=False)
        done = []

        def f():
            while True:
                try:
                    stackless.schedule_remove()
                except TestError:
                    done.append(True)
        t = stackless.tasklet(f)()
        stackless.run()
        self.addCleanup(t.kill)
        for ret in self.checkSignatureNamedArgs(t.throw, 1, None, "exc", TestError, "val", None, "tb", None, "pending", False):
            self.assertIsNone(ret)
        self.assertTrue(done)

    def testSig_kill(self):
        # kill(pending=False)
        t = stackless.tasklet(nop)()
        t.tempval = 1
        for ret in self.checkSignatureNamedArgs(t.kill, 0, None, "pending", False):
            self.assertIsNone(ret)
            t = stackless.tasklet(nop)()

    def testSig_set_atomic(self):
        # set_atomic(flag)
        # Stackless: keyword argument not supported
        t = stackless.tasklet()
        for ret in self.checkSignatureNamedArgs(t.set_atomic, 1, None, "flag", False):
            self.assertIsInstance(ret, bool)

    def testSig_bind_thread(self):
        # bind_thread([thread_id])
        # Stackless: keyword argument not supported
        t = stackless.tasklet(nop, ())
        for ret in self.checkSignatureNamedArgs(t.bind_thread, 0, None, "thread_id", -1):
            self.assertIsNone(ret)

    def testAttr_prev_next(self):
        t = stackless.tasklet()
        self.addCleanup(t.kill)
        self.assertIsNone(t.prev)
        self.assertIsNone(t.next)
        t.bind(nop)
        self.assertIsNone(t.prev)
        self.assertIsNone(t.next)
        t()
        self.assertIs(stackless.main, t.prev)
        self.assertIs(stackless.current, t.next)
        t2 = stackless.tasklet(nop)()
        self.addCleanup(t2.kill)
        self.assertIs(stackless.current, t.prev)
        self.assertIs(t2, t.next)
        self.assertIs(t, t2.prev)
        self.assertIs(stackless.current, t2.next)

    #
    # Test state transitions from stackless/tasklets.html#tasklet-life-cycle
    #
    def check_flag(self, tlet, name, expected):
        if expected == "ignore":
            return
        flag = getattr(tlet, name)
        expected = bool(expected)
        self.assertIs(expected, flag,
                      'Expected tasklet flag "{0}" to be {1} but it is {2}'.format(name, expected, flag))

    def check_tasklet_flags(self, tlet,
                            alive=False,
                            paused=False,
                            blocked=False,
                            scheduled=False,
                            restorable=False,
                            atomic=False,
                            block_trap=False,
                            ignore_nesting=False,
                            is_current=False,
                            is_main=False,
                            **kw
                            ):
        self.check_flag(tlet, "alive", alive)
        self.check_flag(tlet, "paused", paused)
        self.check_flag(tlet, "blocked", blocked)
        self.check_flag(tlet, "scheduled", scheduled)
        self.check_flag(tlet, "restorable", restorable)
        self.check_flag(tlet, "atomic", atomic)
        self.check_flag(tlet, "block_trap", block_trap)
        self.check_flag(tlet, "ignore_nesting", ignore_nesting)
        self.check_flag(tlet, "is_current", is_current)
        self.check_flag(tlet, "is_main", is_main)

    def assert_state_notalive(self, tlet, **kw):
        kw.setdefault("restorable", True)
        self.check_tasklet_flags(tlet, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def assert_state_bound(self, tlet, func, **kw):
        kw.setdefault("restorable", True)
        self.check_tasklet_flags(tlet, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIs(func, tlet.tempval)

    def assert_state_scheduled(self, tlet, **kw):
        kw.setdefault("alive", True)
        kw.setdefault("scheduled", True)
        kw.setdefault("restorable", True)
        self.check_tasklet_flags(tlet, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def assert_state_paused(self, tlet, **kw):
        kw.setdefault("alive", True)
        kw.setdefault("paused", True)
        kw.setdefault("restorable", True)
        self.check_tasklet_flags(tlet, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def assert_state_current(self, tlet, **kw):
        kw.setdefault("alive", True)
        kw.setdefault("is_current", True)
        kw.setdefault("scheduled", True)
        kw.setdefault("restorable", True)
        self.check_tasklet_flags(tlet, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def assert_state_scheduler(self, tlet, **kw):
        """tasklet has called stackless.run()"""
        kw.setdefault("alive", True)
        kw.setdefault("paused", True)
        self.check_tasklet_flags(tlet, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def assert_state_blocked(self, tlet, **kw):
        kw.setdefault("alive", True)
        kw.setdefault("scheduled", True)
        kw.setdefault("blocked", True)
        kw.setdefault("restorable", True)
        self.check_tasklet_flags(tlet, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def testLC_initial_notalive(self):
        # change state
        t = stackless.tasklet()
        # check state
        self.assert_state_notalive(t)

    def testLC_initial_bound(self):
        # change state
        t = stackless.tasklet(nop)
        # check state
        self.assert_state_bound(t, nop)

    def testLC_notalive_bound(self):
        # prepare
        t = stackless.tasklet()
        # check state
        self.assert_state_notalive(t)
        # change state
        t.bind(nop)
        # check state
        self.assert_state_bound(t, nop)

    def testLC_bound_notalive(self):
        # prepare
        t = stackless.tasklet()
        t.bind(nop)
        # check state
        self.assert_state_bound(t, nop)
        # change state
        t.bind(None)
        # check state
        self.assert_state_notalive(t)

        # second variant: bind()
        # prepare
        t = stackless.tasklet()
        t.bind(nop)
        # check state
        self.assert_state_bound(t, nop)
        # change state
        t.bind()
        # check state
        self.assert_state_notalive(t)

    def testLC_bound_scheduled(self):
        # prepare
        t = stackless.tasklet()
        t.bind(nop)
        # check state
        self.assert_state_bound(t, nop)
        # change state
        t.setup()
        # check state
        self.assert_state_scheduled(t)

        # Variant. use __call__
        # prepare
        t = stackless.tasklet()
        t.bind(nop)
        # check state
        self.assert_state_bound(t, nop)
        # change state
        t()
        # check state
        self.assert_state_scheduled(t)

    def testLC_scheduled_paused(self):
        # prepare
        t = stackless.tasklet(nop)()
        # check state
        self.assert_state_scheduled(t)
        # change state
        t.remove()
        # check state
        self.assert_state_paused(t)

    def testLC_scheduled_notalive(self):
        # prepare
        t = stackless.tasklet(nop)()
        # check state
        self.assert_state_scheduled(t)
        # change state
        t.kill()
        # check state
        self.assert_state_notalive(t)

    def testLC_paused_scheduled(self):
        # prepare
        t = stackless.tasklet().bind(nop, ())
        # check state
        self.assert_state_paused(t)
        # change state
        t.insert()
        # check state
        self.assert_state_scheduled(t)

        # Variant using kill(pending=True)
        # prepare
        t = stackless.tasklet().bind(nop, ())
        # check state
        self.assert_state_paused(t)
        # change state
        t.kill(pending=True)
        # check state
        self.assert_state_scheduled(t, tempval="ignore")

    def testLC_notalive_paused(self):
        # prepare
        t = stackless.tasklet()
        # check state
        self.assert_state_notalive(t)
        # change state
        t.bind(nop, ())
        # check state
        self.assert_state_paused(t)

        # Variant bind with 3 args
        # prepare
        t = stackless.tasklet()
        # check state
        self.assert_state_notalive(t)
        # change state
        t.bind(nop, (), {})
        # check state
        self.assert_state_paused(t)

        # Variant bind with kwargs
        # prepare
        t = stackless.tasklet()
        # check state
        self.assert_state_notalive(t)
        # change state
        t.bind(nop, kwargs={})
        # check state
        self.assert_state_paused(t)

    def testLC_paused_notalive(self):
        # prepare
        t = stackless.tasklet().bind(nop, ())
        # check state
        self.assert_state_paused(t)
        # change state
        t.bind()
        # check state
        self.assert_state_notalive(t)

        # Variant bind(None)
        # prepare
        t = stackless.tasklet().bind(nop, ())
        # check state
        self.assert_state_paused(t)
        # change state
        t.bind(None)
        # check state
        self.assert_state_notalive(t)

        # Variant kill()
        # prepare
        t = stackless.tasklet().bind(nop, ())
        # check state
        self.assert_state_paused(t)
        # change state
        t.kill()
        # check state
        self.assert_state_notalive(t)

    def testLC_paused_current_notalive(self):
        # prepare
        t = stackless.tasklet()
        result = []

        def f_run(self, other_tlet):
            self.assert_state_current(t)
            self.assert_state_scheduled(other_tlet, is_main=True, restorable="ignore")
            result.append(0)
        t.bind(f_run, (self, stackless.current))
        # check state
        self.assert_state_paused(t)
        # change state
        t.run()
        # check state
        self.assertListEqual([0], result)
        self.assert_state_notalive(t)

        # Variant using switch
        def f_switch(self, other_tlet):
            self.assert_state_current(t)
            self.assert_state_paused(other_tlet, is_main=True, restorable="ignore")
            result.append(1)

        del result[:]
        t.bind(f_switch, (self, stackless.current))
        # check state
        self.assert_state_paused(t)
        # change state
        t.switch()
        # check state
        self.assertListEqual([1], result)
        self.assert_state_notalive(t)

    def testLC_scheduled_current_notalive(self):
        # prepare
        t = stackless.tasklet()
        result = []

        def f_run(self, other_tlet):
            self.assert_state_current(t)
            self.assert_state_scheduled(other_tlet, is_main=True, restorable="ignore")
            result.append(0)
        t.bind(f_run).setup(self, stackless.current)
        # check state
        self.assert_state_scheduled(t)
        # change state
        t.run()
        # check state
        self.assertListEqual([0], result)
        self.assert_state_notalive(t)

        # Variant using switch
        def f_switch(self, other_tlet):
            self.assert_state_current(t)
            self.assert_state_paused(other_tlet, is_main=True, restorable="ignore")
            result.append(1)

        del result[:]
        t.bind(f_switch).setup(self, stackless.current)
        # check state
        self.assert_state_scheduled(t)
        # change state
        t.switch()
        # check state
        self.assertListEqual([1], result)
        self.assert_state_notalive(t)

        # Variant using stackless.run
        def f_stackless_run(self, other_tlet):
            self.assert_state_current(t)
            self.assert_state_scheduler(other_tlet, is_main=True)
            result.append(2)

        del result[:]
        t.bind(f_stackless_run).setup(self, stackless.current)
        # check state
        self.assert_state_scheduled(t)
        # change state
        stackless.run()
        # check state
        self.assertListEqual([2], result)
        self.assert_state_notalive(t)

    def testLC_current_notalive(self):
        # prepare
        t = stackless.tasklet()
        result = []

        def f_kill(self):
            # check state
            self.assert_state_current(t)
            result.append(0)
            # change state
            t.kill()

        t.bind(f_kill).setup(self)
        self.assert_state_scheduled(t)
        t.run()

        # check state
        self.assertListEqual([0], result)
        self.assert_state_notalive(t)

    def testLC_current_blocked_scheduled(self):
        # prepare
        t = stackless.tasklet()
        result = []
        c = stackless.channel()

        def f_send(self):
            # check state
            self.assert_state_current(t)
            result.append(0)
            # change state
            c.send(123)

        t.bind(f_send).setup(self)
        self.assert_state_scheduled(t)
        t.run()

        # check state
        self.assertListEqual([0], result)
        self.assert_state_blocked(t, tempval="ignore")
        # change state
        self.assertEqual(123, c.receive())
        # check state
        self.assert_state_scheduled(t)
        # cleanup
        t.kill()
        self.assert_state_notalive(t)
        del result[:]

        # Variant using receive
        def f_receive(self):
            # check state
            self.assert_state_current(t)
            result.append(1)
            # change state
            self.assertEqual(456, c.receive())

        t.bind(f_receive).setup(self)
        self.assert_state_scheduled(t)
        t.run()

        # check state
        self.assertListEqual([1], result)
        self.assert_state_blocked(t)
        # change state
        c.send(456)
        # check state
        self.assert_state_notalive(t)
        del result[:]

        # Variant using send_throw
        def f_send_throw(self):
            # check state
            self.assert_state_current(t)
            result.append(2)
            # change state
            c.send_throw(TestError("f_send_throw"))

        t.bind(f_send_throw).setup(self)
        self.assert_state_scheduled(t)
        t.run()

        # check state
        self.assertListEqual([2], result)
        self.assert_state_blocked(t, tempval="ignore")
        # change state
        self.assertRaisesRegex(TestError, "f_send_throw", c.receive)
        # check state
        self.assert_state_scheduled(t)
        # cleanup
        t.kill()
        self.assert_state_notalive(t)
        del result[:]

        # Variant using send_throw
        def f_send_exception(self):
            # check state
            self.assert_state_current(t)
            result.append(3)
            # change state
            c.send_exception(TestError, "f_send_exception")

        t.bind(f_send_exception).setup(self)
        self.assert_state_scheduled(t)
        t.run()

        # check state
        self.assertListEqual([3], result)
        self.assert_state_blocked(t, tempval="ignore")
        # change state
        self.assertRaisesRegex(TestError, "f_send_exception", c.receive)
        # check state
        self.assert_state_scheduled(t)
        # cleanup
        t.kill()
        self.assert_state_notalive(t)
        del result[:]

    def testLC_blocked_current(self):
        # prepare
        t = stackless.tasklet()
        result = []
        c = stackless.channel()

        def f_receive(self):
            self.assertEqual(123, c.receive())
            self.assert_state_current(t)
            result.append(0)

        t.bind(f_receive).setup(self)
        self.assert_state_scheduled(t)
        t.run()

        # check state
        self.assert_state_blocked(t)
        # change state
        c.send(123)
        result.append(1)
        # check state
        self.assertListEqual([0, 1], result)
        self.assert_state_notalive(t)
        del result[:]

        # Variant with send
        # prepare
        def f_send(self):
            c.send(123)
            self.assert_state_current(t)
            result.append(0)

        c.preference = 1
        t.bind(f_send).setup(self)
        self.assert_state_scheduled(t)
        t.run()

        # check state
        self.assert_state_blocked(t, tempval="ignore")
        # change state
        self.assertEqual(123, c.receive())
        result.append(1)
        # check state
        self.assertListEqual([0, 1], result)
        self.assert_state_notalive(t)
        del result[:]

    #
    # Test various error conditions
    #
    def test_unbind_scheduled(self):
        # prepare
        t = stackless.tasklet(nop)()
        # check state
        self.assert_state_scheduled(t)
        # change state
        self.assertRaisesRegex(RuntimeError, "tasklet is scheduled", t.bind)

        # prepare
        t = stackless.tasklet(nop)()
        # check state
        self.assert_state_scheduled(t)
        # change state
        self.assertRaisesRegex(RuntimeError, "tasklet is scheduled", t.bind, None)
