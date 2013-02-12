"""Test the debugger
"""

from __future__ import division

from pytest import skip

try:
    import urwid
except ImportError:
    raise skip('no urwid')

from gillcup_graphics import debugger


class DebugTreeWalker(debugger.TreeWalker):
    """A testing TreeWalker subclass"""
    def __init__(self, nested_list):
        super(DebugTreeWalker, self).__init__()
        try:
            iterator = iter(nested_list)
        except TypeError:
            pass
        else:
            self.list = list(DebugTreeWalker(i) for i in iterator)

    def __repr__(self):
        return '<%s>' % self.list

    def check_linearization(self, *positions):
        """Check that tree positions are the as given, validating all links
        """
        assert positions[0] == []
        assert self.prev_position(positions[0]) is None
        assert self.next_position(positions[-1]) is None
        for a, b in zip(positions, positions[1:]):
            self._check_pair(a, b)
        assert self.last_position() == positions[-1]

    def _check_pair(self, a, b):
        assert self.next_position(a) == b
        assert self.prev_position(b) == a

    @property
    def widget(self):
        return urwid.Text(str(self.list))


class TestTreeWalker(object):
    """TreeWalker test class"""
    def test_empty(self):
        """Test an empty TreeWalker"""
        walker = DebugTreeWalker([])
        assert walker.next_position([]) is None
        assert walker.prev_position([]) is None

    def test_one_element(self):
        """Test a simple one-element TreeWalker"""
        walker = DebugTreeWalker([0])
        walker.check_linearization([], [0])

    def test_two_element(self):
        """Test a simple two-element TreeWalker"""
        walker = DebugTreeWalker([0, 1])
        walker.check_linearization([], [0], [1])

    def test_nested_elements(self):
        """Test a simple nested TreeWalker"""
        walker = DebugTreeWalker([0, [1, 2, 3], 4])
        walker[1].check_linearization([], [0], [1], [2])
        walker.check_linearization([], [0], [1], [1, 0], [1, 1], [1, 2], [2])
