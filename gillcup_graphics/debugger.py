#!/usr/bin/env python
# Encoding: UTF-8

"""The Gillcup Graphics debugger

Provides a console interface that allows inspecting live Gillcup Graphics
scenes.

Gillcup Graphics is powered by the Urwid library. (You'll need to install
it manually, as it's not in the requirements)
"""

from __future__ import division, unicode_literals

import urwid
import pyglet
import fractions
import weakref
import collections
import time
import itertools
import math

import gillcup_graphics
import gillcup
import gillcup.effect


GRAYS = [0, 3, 7, 11, 15, 19, 23, 27, 31, 35, 38, 42, 46, 50, 52, 58, 62,
    66, 70, 74, 78, 82, 85, 89, 93, 100]
COLORS = '068adf'

def make_palette():
    """Create an urwid palette for the TUI"""
    fg = 'light gray'
    bg = 'black'
    sel_bg = 'dark blue'

    palette = [
            (None, fg, bg),
            ('selected', fg, sel_bg),
            ('name', 'white', bg),
            ('name selected', 'white', sel_bg),
            ('grayed', 'dark gray', bg),
            ('grayed selected', 'dark gray', sel_bg),
            ('warning', 'light red,bold', bg, 'bold'),
            ('warning selected', 'light red,bold', sel_bg, 'bold'),
        ]
    for gray in GRAYS:
        palette.append(('g%s' % gray, fg, bg, '', 'g%s' % gray, bg))
        palette.append(
            ('g%s selected' % gray, fg, sel_bg, '', 'g%s' % gray, sel_bg))

    for rgb in itertools.product(COLORS, repeat=3):
        colorname = ''.join(rgb)
        palette.append(('rgb-' + colorname, fg, bg, '', '#' + colorname, bg))
        palette.append(('rgb-%s selected' % colorname,
            fg, sel_bg, '', '#' + colorname, sel_bg))

    return palette

default_palette = make_palette()

def make_select_mapping(item):
    """Mapping for fill_attr_apply to get the "selected" palette entries"""
    if item:
        if item.endswith('selected'):
            return item
        return '%s selected' % item
    else:
        return 'selected'


select_mapping = dict((i[0], make_select_mapping(i[0]))
    for i in default_palette)


original_do_draw = gillcup_graphics.GraphicsObject.do_draw
def monkeypatched_do_draw(self, *args, **kwargs):
    """Wrap GraphicsObject.do_draw method with a timer"""
    start = time.time()
    retval = original_do_draw(self, *args, **kwargs)
    elapsed = time.time() - start
    try:
        original = self.debugger__render_time
    except AttributeError:
        self.debugger__render_time = elapsed
    else:
        # Smooth the value over several frames
        self.debugger__render_time = (original * 9 + elapsed) / 10
    return retval
gillcup_graphics.GraphicsObject.do_draw = monkeypatched_do_draw


class Main(urwid.Frame):
    """The main GG Debugger widget"""
    _selectable = True

    def __init__(self, clock, layer):
        self.layer = layer
        self.clock = clock
        self.clock_column = TimeColumn(clock)
        self.scene_column = SceneColumn(clock, [layer])
        self.columns = urwid.Columns([
                self.clock_column,
                self.scene_column,
            ], 1)
        super(Main, self).__init__(self.columns)

    def tick(self, loop, _data):
        """Manual tick for the Pyglet main loop"""
        loop.set_alarm_in(1 / 60, self.tick, None)
        pyglet.clock.tick()

        for window in pyglet.app.windows:
            window.switch_to()
            window.dispatch_events()
            window.dispatch_event('on_draw')
            window.flip()


    def keypress(self, size, key):
        """Global keypress handler"""
        key = super(Main, self).keypress(size, key)
        if not key:
            return
        elif key == ' ':
            self.clock_column.toggle_pause()
        elif key in '-_':
            self.clock_column.speed_down()
        elif key in '+=':
            self.clock_column.speed_up()
        elif key in '0':
            self.clock_column.speed_normal()
        elif key in '.':
            self.clock_column.nudge_clock(1 / 30)
        elif key in '>':
            self.clock_column.nudge_clock(1)
        elif key in 'n':
            self.clock_column.next_action()
        elif key == 'esc':
            raise urwid.ExitMainLoop()
        else:
            return key


class EventListWalker(urwid.ListWalker):
    """Urwid list walker that displays actions scheduled on a clock"""
    def __init__(self, clock):
        super(EventListWalker, self).__init__()
        self.clock = clock
        self.position = 0
        self._modified = self._modified
        clock.schedule_update_function(self._modified)

    def get_at(self, pos):
        """Get a widget and position for action at the specified position"""
        # An undocumented Clock detail is that events are a heapq: although
        # not guaranteed to be sorted, it can be sorted without adverse
        # effects
        clock = self.clock
        clock.events.sort()
        if 0 <= pos < len(clock.events):
            event = clock.events[pos]
            size = len('{0:.3f}'.format(clock.events[-1].time))
            text = '{0:{1}.3f} {2}'.format(
                event.time, size, event.action)
            return urwid.Text(text, wrap='clip'), pos
        else:
            return None, None

    def get_focus(self):
        """Part of the ListWalker interface"""
        return self.get_at(self.position)

    def get_next(self, position):
        """Part of the ListWalker interface"""
        return self.get_at(position + 1)

    def get_prev(self, position):
        """Part of the ListWalker interface"""
        return self.get_at(position - 1)

    def set_focus(self, position):
        """Part of the ListWalker interface"""
        self.position = position
        self._modified()


class TimeColumn(urwid.Frame):
    """Widget with time-and clock-related info"""
    def __init__(self, clock):
        self.clock = clock
        self.event_view = urwid.ListBox(EventListWalker(clock))
        self.clock_header = urwid.Text('')
        super(TimeColumn, self).__init__(self.event_view,
            header=self.clock_header)
        # Reify the method as we need to keep a reference to it
        self._set_text = self._set_text
        clock.schedule_update_function(self._set_text)
        self.paused = False
        self.clock_speed = fractions.Fraction(1)

    def _set_text(self):  # pylint: disable=E0202
        """Set the right text for the header"""
        if self.paused:
            speed_str = '❚❚ '
        else:
            speed_str = ' ▶ '
        self.clock_speed = fractions.Fraction(self.clock_speed)
        if self.clock_speed.numerator != 1:
            speed_str += '×{}'.format(self.clock_speed.numerator)
        if self.clock_speed.denominator != 1:
            speed_str += '÷{}'.format(self.clock_speed.denominator)
        self.clock_header.set_text('t={0:.3f}  (at {1:.1f} fps)\n{2}'.format(
            self.clock.time, pyglet.clock.get_fps(), speed_str))
        self._invalidate()

    def toggle_pause(self):
        """Toggle the clock paused/advancing mode"""
        self.paused = not self.paused
        self.update_clock_speed()

    def speed_down(self):
        """Set a lower speed on he clock"""
        self.clock_speed /= 2
        self.update_clock_speed()

    def speed_up(self):
        """Set a higher speed on he clock"""
        self.clock_speed *= 2
        self.update_clock_speed()

    def speed_normal(self):
        """Set the 1× speed on the clock"""
        self.clock_speed = 1
        self.update_clock_speed()

    def nudge_clock(self, amount):
        """Advance clock by amount * current speed seconds"""
        self.clock.speed = self.clock_speed
        self.clock.advance(amount)
        self.update_clock_speed()

    def next_action(self):
        """Advance clock to after the nextscheduled action"""
        if self.clock.events:
            self.clock.speed = 1
            difference = self.clock.events[0].time - self.clock.time
            self.clock.advance(difference + 0.00001)
            self.update_clock_speed()

    def update_clock_speed(self):
        """Update the clock's speed to reflect our settings"""
        if self.paused:
            self.clock.speed = 0
        else:
            self.clock.speed = self.clock_speed
        self._set_text()


class TreeWidget(urwid.FlowWidget):
    """Wrap TreeWalker to provide indent etc. handling needed for a treeview
    """
    _selectable = True
    indent_size = 2

    cache = collections.defaultdict(weakref.WeakKeyDictionary)


    def __init__(self, item, indent):
        super(TreeWidget, self).__init__()
        self.item = item
        self.indent = indent * self.indent_size

    @classmethod
    def new(cls, item, indent):
        """Return a cached TreeWidget, or create a new one"""
        try:
            return cls.cache[indent][item]
        except KeyError:
            rv = cls.cache[indent][item] = cls(item, indent)
            return rv

    def rows(self, size, focus=False):
        """Return no. of rows required for the given size"""
        [maxcol] = size
        maxcol -= self.indent
        return self.item.widget.rows((maxcol, ), focus)

    def render(self, size, focus=False):
        """Render the widget into a Canvas"""
        [cols] = size
        indent = self.indent
        if indent >= cols:
            return urwid.SolidCanvas(' ', cols, self.rows(size, focus))
        orig_canvas = self.item.widget.render((cols - indent, ), focus)
        canvas = urwid.CompositeCanvas(orig_canvas)
        canvas.pad_trim_left_right(indent, 0)
        if indent:
            if len(self.item.list):
                if self.item.expanded:
                    char = '▾'
                else:
                    char = '▸'
            else:
                char = '·'
            overlay = urwid.Text(('grayed', char)).render((1,))
            overlay = urwid.CompositeCanvas(overlay)
            canvas.overlay(overlay, indent - self.indent_size, 0)
        if focus:
            canvas.fill_attr_apply(select_mapping)
        return canvas

    def keypress(self, size, key):  # pylint: disable=W0613
        """Handle key presses – list selection"""
        if key == 'right':
            if self.item.expanded:
                if len(self.item.list):
                    return 'down'
            else:
                self.item.expanded = True
            self._invalidate()
        elif key == 'left':
            if self.item.expanded:
                self.item.expanded = False
            self._invalidate()
        else:
            return key


class TreeWalker(urwid.ListWalker):
    """A ListWalker that handles trees of objects

    This class is used for all nodes of the tree.

    Each TreeWalker instance has a (possibly dynamic) list of children in its
    `list` attribute. The children can be are arbitrary objects; if they aren't
    TreeWalkers, the `wrap_child` method must be overriden to wrap a child
    with a suitable TreeWalker subclass.

    The TreeWalkers are cached in a WeakKeyDictionary. This allows their
    `expanded` state to persist. If children are not weak-referencable, set the
    cache_class class attribute to `dict`.

    Positions in the tree are represented as a list of indices into the
    children lists of successive nodes. Such positions are only valid as long
    as the children lists don't change. Persistent positions – lists of
    successive child items themselves – are also available.

    The Urwid "focus" is only stored on the TreeWalker that is used directly in
    a list widget (i.e. usually the topmost one).

    :param obj: Optional object to store in the `obj` attribute
    """
    list = ()
    expanded = True
    cache_class = weakref.WeakKeyDictionary

    def __init__(self, obj=None):
        super(TreeWalker, self).__init__()
        self.persistent_position = []
        self.cache = self.cache_class()
        self.obj = obj

    def get_item(self, position):
        """Get the (sub-(sub-(…)))item identified by position"""
        if position:
            return self[position[0]].get_item(position[1:])
        else:
            return self

    def _get_at(self, position):
        """Get a tree widget and position for the given position

        The returned pair is suitable for returning from the list walker
        protocol methods such as get_next
        """
        if position is None:
            return None, None
        else:
            item = self.get_item(position)
            return TreeWidget.new(item, len(position)), position

    def next_position(self, position):
        """Calculate position of the item to be displayed after the given one
        """
        if position:
            # Recurse into the children list
            index = position[0]
            pos = self[index].next_position(position[1:])
            if pos is not None:
                # Handled entirely in children
                return [index] + pos
            elif index + 1 < len(self):
                # Next item wasn't in the children; return next sibling
                return [index + 1]
            else:
                # Next item wasn't in the children; no next sibling
                return None
        elif len(self):
            # Return the first child
            return [0]
        else:
            # No children – the next item isn't in this list
            return None

    def prev_position(self, position):
        """Calculate position of the item to be displayed before the given one
        """
        if position:
            # Recurse into children
            index = position[0]
            pos = self[index].prev_position(position[1:])
            if pos is not None:
                # Handled entirely in children
                return [index] + pos
            elif index > 0:
                # Prev item not in children; return last item of prev sibling
                return [index - 1] + self[index - 1].last_position()
            else:
                # Prev item not in children; no prev sibling: return self
                return []
        else:
            # Previous item is not in this subtree
            return None

    def last_position(self):
        """Calculate position of the last item displayed in this subtree
        """
        if len(self):
            last = len(self) - 1
            return [last] + self[last].last_position()
        else:
            return []

    def get_next(self, position):
        """Return item and position next to the given one.

        Part of ListWalker interface"""
        return self._get_at(self.next_position(position))

    def get_prev(self, position):
        """Return item and position previous to the given one.

        Part of ListWalker interface"""
        return self._get_at(self.prev_position(position))

    def get_focus(self):
        """Return item and position of the current focus

        Part of ListWalker interface

        The focus is stored as a "persistent position" to allow for changes in
        the underlying tree
        """
        position = self.get_indexed_position(self.persistent_position)
        return self._get_at(position)

    def set_focus(self, position):
        """Set the current focus position

        Part of ListWalker interface

        The focus is stored as a "persistent position" to allow for changes in
        the underlying tree
        """
        self.persistent_position = self.get_persistent_position(position)
        self._modified()

    def get_persistent_position(self, position):
        """Return "persistent position" corresponding to the given position

        The persistent position is a list of (item, index) pairs.
        """
        if position:
            pos = position[0]
            item = self.list[pos]
            tail = position[1:]
            return [(item, pos)] + self[pos].get_persistent_position(tail)
        else:
            return []

    def get_indexed_position(self, persistent_position):
        """Return "normal" position corresponding to given persistent position

        The persistent position is a list of (item, index) pairs. If the item
        is not found, something close to the index is returned (otherwise the
        index is ignored).
        """
        if persistent_position:
            item, pos = persistent_position[0]
            try:
                pos = self.list.index(item)
            except ValueError:
                # The item the persistent position referred to was deleted!
                if pos < len(self):
                    return [pos]
                else:
                    if len(self):
                        return [len(self) - 1]
                    else:
                        return []
            else:
                tail = persistent_position[1:]
                return [pos] + self[pos].get_indexed_position(tail)
        else:
            return []

    def __len__(self):
        """Length of the children list, as displyed

        If the tree is collapsed, len returns zero.
        """
        if self.expanded:
            return len(self.list)
        else:
            return 0

    def __getitem__(self, pos):
        """Get a ListWalker corresponding to the item at the given index"""
        item = self.list[pos]
        try:
            return self.cache[item]
        except KeyError:
            rv = self.cache[item] = self.wrap_child(item)
            return rv

    def wrap_child(self, item):
        """Return a ListWalker corresponding to thegiven child"""
        return item

    @property
    def widget(self):
        """Urwid widget to display at this tree's root"""
        raise NotImplementedError()


class SceneGraphWalker(TreeWalker):
    """Root of the scene graph tree"""
    def __init__(self, clock, layers):
        super(SceneGraphWalker, self).__init__()
        self.layers = layers
        self._modified = self._modified
        clock.schedule_update_function(self._modified)

    @property
    def widget(self):
        return urwid.Text('Layers', wrap='clip')

    @property
    def list(self):
        """List the layers"""
        return self.layers

    def wrap_child(self, item):
        return GraphicsObjectWalker(item)


class NonCachedText(urwid.Text):
    """Like urwid.Text, but doesn't cache its canvas"""
    def render(self, size, focus=False):
        rv = super(NonCachedText, self).render(size, focus)
        self._invalidate()
        return rv


class GraphicsObjectWidget(NonCachedText):
    """Widget that displays data for a GraphicsObject"""
    no_cache = ['render']

    def __init__(self, obj):
        super(GraphicsObjectWidget, self).__init__('')
        self.obj = obj
        self._row_cache = [None] * 2

    def parts(self):
        """Return a list of parts that make up the info in this widget

        Returns a list of triples with these elements:

            - separator: text to put before the element if a line dowsn't begin
                with it
            - justification mark; '<' to aligh right, '>' to align left
            - attribute: attribute for the text, or None
            - the text itself
        """
        obj = self.obj
        name_part = obj.name or ''
        render_time = getattr(obj, 'debugger__render_time', None)
        type_part = '({0})'.format(type(obj).__name__)
        time_attr = None
        if render_time is None:
            time_part = ''
        else:
            time_part = '{0:.1f}ms'.format(render_time * 1000)
            if render_time < 0.005:
                index = render_time / 0.005 * 2 / 3 + 1 / 3
                sz = len(GRAYS)
                time_attr = 'g%s' % GRAYS[int(sz * index)]
            elif render_time < 0.01:
                index = (render_time - 0.005) / 0.005
                sz = len(COLORS)
                time_attr = 'rgb-ff%s' % COLORS[-int(sz * index) - 1]
            else:
                sz = len(COLORS)
                index = math.log(render_time) - math.log(0.01)
                if index >= 1:
                    time_attr = 'warning'
                else:
                    time_attr = 'rgb-f%s0' % COLORS[-int(sz * index) - 1]
        return [
                ('', '<', 'name', name_part),
                (' ' if name_part else '', '<', None, type_part),
                (' ', '>', time_attr, time_part),
            ]

    def update_text(self, size):
        """Update this widget's text to match its widget"""
        parts = self.parts()
        cache_key = size, parts
        if cache_key == self._row_cache[0]:
            self.set_text(self._row_cache[1])
            return
        [cols] = size
        row_parts = []
        col = 0
        rows = [row_parts]
        for sep, just, attr, text in parts:
            col += len(text) + len(sep)
            if row_parts and col > cols:
                row_parts = [(None, '\n')]
                rows.append(row_parts)
                col = len(text)
            else:
                if sep:
                    row_parts.append((None, sep))
            if just == '>':
                row_parts.append((None, None))
            if text:
                row_parts.append((attr, text))
        for row in rows:
            fill_count = sum(1 for attr, text in row if text is None)
            text_length = sum(len(text) for attr, text in row if text)
            total_fill_len = cols - text_length
            col = 0
            for i, (attr, text) in enumerate(row):
                if text is None:
                    text = ' ' * int(total_fill_len / fill_count)
                    row[i] = (None, text)
                if col + len(text) > cols:
                    text = text[:max(0, cols - col)]
                    row[i] = (attr, text)
                col += len(text)
            if not fill_count:
                row.append(' ' * total_fill_len)
        self._row_cache = cache_key, rows
        self.set_text(rows)

    def rows(self, size, focus=False):
        """Return number of rows the widget takes up with the given no. of cols
        """
        self.update_text(size)
        return super(GraphicsObjectWidget, self).rows(size, focus)

    def render(self, size, focus=False):
        """Return number of rows the widget takes up with the given no. of cols
        """
        self.update_text(size)
        return super(GraphicsObjectWidget, self).render(size, focus)


class GraphicsObjectWalker(TreeWalker):
    """TreeWalker for a graphics object

    Has up to two children: a tree of property info and a tree of child info
    The child info is only present when the child list is not an ampty tuple
    (this indicates that the widget can't have children). In this case, the
    tree is not expanded by default.
    """
    def __init__(self, obj):
        self.list = [PropertiesWalker(obj)]
        if obj.children != ():
            self.list.append(ChildrenWalker(obj))
        else:
            self.expanded = False
        super(GraphicsObjectWalker, self).__init__(obj)

    @property
    def widget(self):
        return GraphicsObjectWidget(self.obj)


class ChildrenWalker(TreeWalker):
    """TreeWalker for the list of a GraphicsObject's children"""
    @property
    def list(self):
        """Just the list of children"""
        return self.obj.children

    @property
    def widget(self):
        widget = NonCachedText('children (%s)' % len(self.obj.children))
        if not self.obj.children:
            widget = urwid.AttrWrap(widget, 'grayed')
        return widget

    def wrap_child(self, item):
        return GraphicsObjectWalker(item)


class PropertiesWalker(TreeWalker):
    """TreeWalker for the list of an object's animated properties"""
    cache_class = dict
    names_cache = dict()

    expanded = False

    @property
    def list(self):
        """Return names of animated properties on this object

        Exclude TupleProperty subproperties (if the parent is also on the
        object)
        """
        cls = type(self.obj)
        all_names = dir(cls)
        try:
            # Check if dir() still returns the same; if it does, return cached
            # property names.
            # XXX: This isn't 100% robust – if someone switches a non-animated
            # property for an animated one, or vice versa, we won't notice the
            # change
            names, check_all_names = self.names_cache[cls]
            if all_names == check_all_names:
                return names
        except KeyError:
            pass
        # We collect all AnimatedProperties, but filter out subproperties
        props = {}
        subprops = set()
        for name in all_names:
            prop = getattr(cls, name)
            if isinstance(prop, gillcup.AnimatedProperty):
                props[prop] = name
                try:
                    subproperties = prop.subproperties
                except AttributeError:
                    pass
                else:
                    subprops.update(subproperties)
        names = sorted(v for k, v in props.iteritems() if k not in subprops)
        self.names_cache[cls] = names, all_names
        return names

    @property
    def widget(self):
        return urwid.AttrWrap(urwid.Text('properties'),  'grayed')

    def wrap_child(self, item):
        return PropertyWalker(self.obj, item)


class PropertyWalker(TreeWalker):
    """TreeWaler for an individual animated property"""
    expanded = False

    def __init__(self, obj, name):
        super(PropertyWalker, self).__init__(obj)
        self.name = name
        self.prop = getattr(type(obj), name)

    @property
    def list(self):
        """List effects on this property, traversing the "parent" chain"""
        effects = []
        effect = self.prop.get_effect(self.obj)
        while effect:
            effects.append(effect)
            try:
                effect = effect.parent
            except AttributeError:
                effect = None
        return effects

    @property
    def widget(self):
        value = getattr(self.obj, self.name)
        widget = NonCachedText([self.name, ' ', str(value)])
        effect = self.prop.get_effect(self.obj)
        try:
            is_constant = effect.is_constant
        except AttributeError:
            is_constant = False
        if is_constant:
            widget = urwid.AttrWrap(widget, 'grayed')
        return widget

    def wrap_child(self, item):
        return EffectWalker(item)


class EffectWalker(PropertiesWalker):
    """TreeWaler for an effect"""
    @property
    def widget(self):
        obj = self.obj
        name = getattr(obj, 'name', None)
        if name:
            name_part = name + ' '
        else:
            name_part = ''
        text = [('name', name_part), '({0})'.format(type(obj).__name__)]
        return urwid.Text(text, wrap='clip')


class SceneColumn(urwid.Frame):
    """Widget to show the scene graph info"""
    def __init__(self, clock, layers):
        self.layers = layers
        self.clock = clock
        self.event_view = urwid.ListBox(SceneGraphWalker(clock, layers))
        self.clock_header = urwid.Text('')
        super(SceneColumn, self).__init__(self.event_view,
            header=self.clock_header)
        self._invalidate = self._invalidate
        clock.schedule_update_function(self._invalidate)


def run(clock, layer, *args, **kwargs):
    """Run the given layer in the debugger

    The `args` and `kwargs` get passed to gillcup_graphics.Window
    """
    main = Main(clock, layer)
    loop = urwid.MainLoop(main, palette=default_palette)
    loop.screen.set_terminal_properties(colors=256)
    loop.set_alarm_in(1 / 30, main.tick, None)
    gillcup_graphics.Window(layer, *args, **kwargs)
    loop.run()

def demo():
    """Some kind of demo to test(/show off?) the debugger"""
    import random
    layer = gillcup_graphics.Layer(name='Base')
    clock = gillcup_graphics.RealtimeClock()
    r = random.random
    def _make_random_rect(parent=layer, d=0):
        rect = gillcup_graphics.Rectangle(parent, relative_anchor=(0.5, 0.5),
            size=(r() * 0.1, r() * 0.1), rotation=r() * 360,
            position=(r() + d, r() + d), color=(r(), r(), r()))
        clock.schedule(gillcup.Animation(rect, 'rotation', r() * 180 - 90,
            time=1, timing='infinite', dynamic=True))
        return rect
    for dummy in range(10):
        _make_random_rect()
    rect = gillcup_graphics.Rectangle(layer, name='Big rect',
        relative_anchor=(0.5, 0.5), position=(0.5, 0.5), size=(0.5, 0.5))
    rotating_layer = gillcup_graphics.Layer(layer, name='Rotating layer',
        anchor=(0.5, 0.5), position=(0.5, 0.5), scale=1.5)
    clock.schedule(gillcup.Animation(rect, 'rotation', 180, time=10,
        timing='infinite'))
    clock.schedule(gillcup.Animation(rotating_layer, 'rotation', -180, time=10,
        timing='infinite'))
    def _next_waypoint():
        clock.schedule(_next_waypoint, 1)
        clock.schedule(gillcup.Animation(rect, 'position', r(), r(), time=5))
        new_rect = _make_random_rect(rotating_layer, -0.5)
        new_rect.opacity = 0
        clock.schedule(gillcup.Animation(new_rect, 'opacity', 1, time=1))
        new_rect.name = 'R{0}'.format(clock.time)
    def _delete_random_rect():
        if not rotating_layer.children:
            return
        victim = random.choice(rotating_layer.children)
        clock.schedule(gillcup.Animation(victim, 'size', 0, time=1 + r()) +
            victim.die)
    def _next_deletion():
        clock.schedule(_next_deletion, 1 + r())
        _delete_random_rect()
    def _next_masskill():
        clock.schedule(_next_masskill, 10)
        for dummy in rotating_layer.children[5:]:
            _delete_random_rect()
    _next_waypoint()
    _next_deletion()
    _next_masskill()

    run(clock, layer, resizable=True)

if __name__ == '__main__':
    demo()
