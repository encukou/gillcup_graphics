"""Test the debugger
"""

from __future__ import division

import pytest

try:
    import urwid
except ImportError:
    raise pytest.skip('no urwid')

from gillcup_graphics import debugger


class DebugTreeWalker(debugger.TreeWalker):
    def __init__(self, nested_list):
        super(DebugTreeWalker, self).__init__()
        try:
            iterator = iter(nested_list)
        except TypeError:
            pass
        else:
            self.list = list(DebugTreeWalker(i) for i in iterator)
        self.widget = str(nested_list)

    def __repr__(self):
        return '<%s>' % self.widget

    def check_linearization(self, *items):
        assert items[0] == []
        assert self.prev_position(items[0]) == None
        assert self.next_position(items[-1]) == None
        for a, b in zip(items, items[1:]):
            self._check_pair(a, b)
        assert self.last_position() == items[-1]

    def _check_pair(self, a, b):
        assert self.next_position(a) == b
        assert self.prev_position(b) == a


class TestTreeWalker(object):
    def test_empty(self):
        walker = DebugTreeWalker([])
        assert walker.get_focus() == ('[]', [])
        assert walker.next_position([]) == None
        assert walker.prev_position([]) == None

    def test_one_element(self):
        walker = DebugTreeWalker([0])
        assert walker.get_focus() == ('[0]', [])
        walker.check_linearization([], [0])

    def test_two_element(self):
        walker = DebugTreeWalker([0, 1])
        assert walker.get_focus() == ('[0, 1]', [])
        walker.check_linearization([], [0], [1])

    def test_nested_elements(self):
        walker = DebugTreeWalker([0, [1, 2, 3], 4])
        assert walker.get_focus() == ('[0, [1, 2, 3], 4]', [])
        walker[1].check_linearization([], [0], [1], [2])
        walker.check_linearization([], [0], [1], [1, 0], [1, 1], [1, 2], [2])
