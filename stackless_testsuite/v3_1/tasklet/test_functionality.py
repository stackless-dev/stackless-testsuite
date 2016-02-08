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
import sys
import thread
import threading
import subprocess
from stackless_testsuite.util import StacklessTestCase

if __name__ == '__main__':
    import stackless_testsuite.v3_1.tasklet  # @NoMove @UnusedImport
    __package__ = "stackless_testsuite.v3_1.tasklet"  # @ReservedAssignment

if hasattr(threading, "main_thread"):
    # Python 3.4 and later
    def main_thread_id():
        return threading.main_thread().ident  # @UndefinedVariable
else:
    def main_thread_id():
        return threading._shutdown.__self__.ident  # @UndefinedVariable


def nop(*args, **kw):
    pass


class TaskletTest(StacklessTestCase):
    """Test class tasklet
    """
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
        self.check_tasklet_flags(tlet, restorable=True, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def assert_state_bound(self, tlet, func, **kw):
        self.check_tasklet_flags(tlet, restorable=True, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIs(func, tlet.tempval)

    def assert_state_scheduled(self, tlet, **kw):
        self.check_tasklet_flags(tlet, alive=True, scheduled=True, restorable=True, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def assert_state_paused(self, tlet, **kw):
        self.check_tasklet_flags(tlet, alive=True, paused=True, restorable=True, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def assert_state_current(self, tlet, **kw):
        self.check_tasklet_flags(tlet, alive=True, restorable=True, is_current=True, scheduled=True, **kw)
        if kw.get("tempval") != "ignore":
            self.assertIsNone(tlet.tempval)

    def assert_state_scheduler(self, tlet, **kw):
        """tasklet has called stackless.run()"""
        self.check_tasklet_flags(tlet, alive=True, paused=True, **kw)
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
            self.assert_state_scheduled(other_tlet, is_main=True)
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
            self.assert_state_paused(other_tlet, is_main=True)
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
            self.assert_state_scheduled(other_tlet, is_main=True)
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
            self.assert_state_paused(other_tlet, is_main=True)
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





    def test_unbind_scheduled(self):
        # prepare
        t = stackless.tasklet(nop)()
        # check state
        self.assert_state_scheduled(t)
        # change state
        self.assertRaisesRegexp(RuntimeError, "tasklet is scheduled", t.bind)

        # prepare
        t = stackless.tasklet(nop)()
        # check state
        self.assert_state_scheduled(t)
        # change state
        self.assertRaisesRegexp(RuntimeError, "tasklet is scheduled", t.bind, None)

