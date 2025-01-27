# -*- test-case-name: twisted.trial.test.test_tests -*-
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Definitions of test cases with various interesting error-related behaviors, to
be used by test modules to exercise different features of trial's test runner.

See the L{twisted.trial.test.test_tests} module docstring for details about how
this code is arranged.
"""


from unittest import skipIf

from twisted.internet import defer, protocol, reactor
from twisted.trial import unittest, util


class FoolishError(Exception):
    pass


class FailureInSetUpMixin:
    def setUp(self):
        raise FoolishError("I am a broken setUp method")

    def test_noop(self):
        pass


class SynchronousTestFailureInSetUp(FailureInSetUpMixin, unittest.SynchronousTestCase):
    pass


class AsynchronousTestFailureInSetUp(FailureInSetUpMixin, unittest.TestCase):
    pass


class FailureInTearDownMixin:
    def tearDown(self):
        raise FoolishError("I am a broken tearDown method")

    def test_noop(self):
        pass


class SynchronousTestFailureInTearDown(
    FailureInTearDownMixin, unittest.SynchronousTestCase
):
    pass


class AsynchronousTestFailureInTearDown(FailureInTearDownMixin, unittest.TestCase):
    pass


class FailureButTearDownRunsMixin:
    """
    A test fails, but its L{tearDown} still runs.
    """

    tornDown = False

    def tearDown(self):
        self.tornDown = True

    def test_fails(self):
        """
        A test that fails.
        """
        raise FoolishError("I am a broken test")


class SynchronousTestFailureButTearDownRuns(
    FailureButTearDownRunsMixin, unittest.SynchronousTestCase
):
    pass


class AsynchronousTestFailureButTearDownRuns(
    FailureButTearDownRunsMixin, unittest.TestCase
):
    pass


class TestRegularFail(unittest.SynchronousTestCase):
    def test_fail(self):
        self.fail("I fail")

    def test_subfail(self):
        self.subroutine()

    def subroutine(self):
        self.fail("I fail inside")


class TestAsynchronousFail(unittest.TestCase):
    """
    Test failures for L{unittest.TestCase} based classes.
    """

    text = "I fail"

    def test_fail(self):
        """
        A test which fails in the callback of the returned L{defer.Deferred}.
        """
        d = defer.Deferred()
        d.addCallback(self._later)
        reactor.callLater(0, d.callback, None)
        return d

    def _later(self, res):
        self.fail("I fail later")

    def test_exception(self):
        """
        A test which raises an exception synchronously.
        """
        raise Exception(self.text)


class ErrorTest(unittest.SynchronousTestCase):
    """
    A test case which has a L{test_foo} which will raise an error.

    @ivar ran: boolean indicating whether L{test_foo} has been run.
    """

    ran = False

    def test_foo(self):
        """
        Set C{self.ran} to True and raise a C{ZeroDivisionError}
        """
        self.ran = True
        1 / 0


@skipIf(True, "skipping this test")
class TestSkipTestCase(unittest.SynchronousTestCase):
    pass


class DelayedCall(unittest.TestCase):
    hiddenExceptionMsg = "something blew up"

    def go(self):
        raise RuntimeError(self.hiddenExceptionMsg)

    def testHiddenException(self):
        """
        What happens if an error is raised in a DelayedCall and an error is
        also raised in the test?

        L{test_reporter.ErrorReportingTests.testHiddenException} checks that
        both errors get reported.

        Note that this behaviour is deprecated. A B{real} test would return a
        Deferred that got triggered by the callLater. This would guarantee the
        delayed call error gets reported.
        """
        reactor.callLater(0, self.go)
        reactor.iterate(0.01)
        self.fail("Deliberate failure to mask the hidden exception")

    testHiddenException.suppress = [  # type: ignore[attr-defined]
        util.suppress(
            message=r"reactor\.iterate cannot be used.*", category=DeprecationWarning
        )
    ]


class ReactorCleanupTests(unittest.TestCase):
    def test_leftoverPendingCalls(self):
        def _():
            print("foo!")

        reactor.callLater(10000.0, _)


class SocketOpenTest(unittest.TestCase):
    def test_socketsLeftOpen(self):
        f = protocol.Factory()
        f.protocol = protocol.Protocol
        reactor.listenTCP(0, f)


class TimingOutDeferred(unittest.TestCase):
    def test_alpha(self):
        pass

    def test_deferredThatNeverFires(self):
        self.methodCalled = True
        d = defer.Deferred()
        return d

    def test_omega(self):
        pass


def unexpectedException(self):
    """i will raise an unexpected exception...
    ... *CAUSE THAT'S THE KINDA GUY I AM*

    >>> 1/0
    """


class EventuallyFailingTestCase(unittest.SynchronousTestCase):
    """
    A test suite that fails after it is run a few times.
    """

    n: int = 0

    def test_it(self):
        """
        Run successfully a few times and then fail forever after.
        """
        self.n += 1
        if self.n >= 5:
            self.fail("eventually failing")
