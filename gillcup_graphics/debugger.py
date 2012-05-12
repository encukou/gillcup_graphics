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

import gillcup_graphics
import gillcup
import gillcup.effect

palette = [
        (None, 'light gray', 'black'),
        ('name', 'white', 'black'),
        ('selected', 'light gray', 'dark blue'),
        ('name selected', 'white', 'dark blue'),
        ('grayed', 'dark gray', 'black'),
        ('grayed selected', 'dark gray', 'dark blue'),
    ]

def select_mapping(item):
    """Mapping for fill_attr_apply to get the "selected" palette entries"""
    if item:
        if item.endswith('selected'):
            return item
        return '%s selected' % item
    else:
        return 'selected'


select_mapping = dict((i[0], select_mapping(i[0])) for i in palette)


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
        pyglet.clock.tick()

        for window in pyglet.app.windows:
            window.switch_to()
            window.dispatch_events()
            window.dispatch_event('on_draw')
            window.flip()

        loop.set_alarm_in(1 / 30, self.tick, None)

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
    def __init__(self, clock):
        super(EventListWalker, self).__init__()
        self.clock = clock
        self.position = 0
        self._modified = self._modified
        clock.schedule_update_function(self._modified)

    def get_at(self, pos):
        # An undocumented Clock detail is that events are a heapq: although
        # not guaranteed to be sorted, it can be sorted without adverse
        # effects
        clock.events.sort()
        if 0 <= pos < len(self.clock.events):
            event = clock.events[pos]
            size = len('{0:.3f}'.format(clock.events[-1].time))
            text = '{0:{1}.3f} {2}'.format(
                event.time, size, event.action)
            return urwid.Text(text, wrap='clip'), pos
        else:
            return None, None

    def get_focus(self):
        return self.get_at(self.position)

    def get_next(self, position):
        return self.get_at(position + 1)

    def get_prev(self, position):
        return self.get_at(position - 1)

    def set_focus(self, position):
        self.position = position
        self._modified()


class TimeColumn(urwid.Frame):
    def __init__(self, clock):
        self.clock = clock
        self.event_view = urwid.ListBox(EventListWalker(clock))
        self.clock_header = urwid.Text('')
        super(TimeColumn, self).__init__(self.event_view,
            header=self.clock_header)
        self._set_text = self._set_text
        clock.schedule_update_function(self._set_text)
        self.paused = False
        self.clock_speed = fractions.Fraction(1)

    def _set_text(self):
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
        self.paused = not self.paused
        self.update_clock_speed()

    def speed_down(self):
        self.clock_speed /= 2
        self.update_clock_speed()

    def speed_up(self):
        self.clock_speed *= 2
        self.update_clock_speed()

    def speed_normal(self):
        self.clock_speed = 1
        self.update_clock_speed()

    def nudge_clock(self, amount):
        self.clock.speed = self.clock_speed
        self.clock.advance(amount)
        self.update_clock_speed()

    def next_action(self):
        self.clock.speed = 1
        difference = self.clock.events[0].time - self.clock.time
        self.clock.advance(difference + 0.00001)
        self.update_clock_speed()

    def update_clock_speed(self):
        if self.paused:
            self.clock.speed = 0
        else:
            self.clock.speed = self.clock_speed
        self._set_text()


class TreeWidget(object):
    cache = collections.defaultdict(weakref.WeakKeyDictionary)

    indent_size = 2

    def __init__(self, item, indent):
        self.item = item
        self.indent = indent * self.indent_size

    @classmethod
    def new(cls, item, indent):
        try:
            return cls.cache[indent][item]
        except KeyError:
            rv = cls.cache[indent][item] = cls(item, indent)
            return rv

    def selectable(self):
        return True

    def rows(self, size, focus=False):
        [maxcol] = size
        maxcol -= self.indent
        return self.item.widget.rows((maxcol, ), focus)

    def render(self, size, focus=False):
        [cols] = size
        indent = self.indent
        rows = self.rows(size)
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

    def keypress(self, size, key):
        if key == 'right':
            if self.item.expanded:
                if len(self.item.list):
                    return 'down'
            else:
                self.item.expanded = True
        elif key == 'left':
            if self.item.expanded:
                self.item.expanded = False
        else:
            return key


class TreeWalker(urwid.ListWalker):
    list = ()
    expanded = True
    cache_class = weakref.WeakKeyDictionary

    def __init__(self, obj=None):
        super(TreeWalker, self).__init__()
        self.persistent_position = []
        self.cache = self.cache_class()
        self.obj = obj

    def get_item(self, position):
        if position:
            return self[position[0]].get_item(position[1:])
        else:
            return self

    def get_at(self, position):
        if position is None:
            return None, None
        else:
            item = self.get_item(position)
            return TreeWidget.new(item, len(position)), position

    def next_position(self, position):
        if position:
            index = position[0]
            pos = self[index].next_position(position[1:])
            if pos is not None:
                return [index] + pos
            elif index + 1 < len(self):
                return [index + 1]
            else:
                return None
        elif len(self):
            return [0]
        else:
            return None

    def prev_position(self, position):
        if position:
            index = position[0]
            pos = self[index].prev_position(position[1:])
            if pos is not None:
                return [index] + pos
            elif index > 0:
                return [index - 1] + self[index - 1].last_position()
            else:
                return []
        else:
            return None

    def last_position(self):
        if len(self):
            last = len(self) - 1
            return [last] + self[last].last_position()
        else:
            return []

    def get_next(self, position):
        return self.get_at(self.next_position(position))

    def get_prev(self, position):
        return self.get_at(self.prev_position(position))

    def get_focus(self):
        position = self.get_indexed_position(self.persistent_position)
        return self.get_at(position)

    def set_focus(self, position):
        self.persistent_position = self.get_persistent_position(position)
        self._modified()

    def get_persistent_position(self, position):
        if position:
            pos = position[0]
            item = self.list[pos]
            tail = position[1:]
            return [(item, pos)] + self[pos].get_persistent_position(tail)
        else:
            return []

    def get_indexed_position(self, persistent_position):
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
        if self.expanded:
            return len(self.list)
        else:
            return 0

    def __getitem__(self, pos):
        item = self.list[pos]
        try:
            return self.cache[item]
        except KeyError:
            rv = self.cache[item] = self.make_child(item)
            return rv

    def make_child(self, item):
        return item


class SceneGraphWalker(TreeWalker):
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
        return self.layers

    def make_child(self, item):
        return GraphicsObjectWalker(item)


class GraphicsObjectWalker(TreeWalker):
    def __init__(self, obj):
        self.list = [PropertiesWalker(obj)]
        if obj.children != ():
            self.list.append(ChildrenWalker(obj))
        else:
            self.expanded = False
        super(GraphicsObjectWalker, self).__init__(obj)

    @property
    def widget(self):
        obj = self.obj
        if obj.name:
            name_part = obj.name + ' '
        else:
            name_part = ''
        text = [('name', name_part), '({0})'.format(type(obj).__name__)]
        return urwid.Text(text, wrap='clip')


class ChildrenWalker(TreeWalker):
    @property
    def list(self):
        return self.obj.children

    @property
    def widget(self):
        widget = urwid.Text('children (%s)' % len(self.obj.children))
        if not self.obj.children:
            widget = urwid.AttrWrap(widget, 'grayed')
        return widget

    def make_child(self, item):
        return GraphicsObjectWalker(item)


class PropertiesWalker(TreeWalker):
    cache_class = dict
    names_cache = dict()

    expanded = False

    @property
    def list(self):
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
                    subprops.update(prop.subproperties)
        names = sorted(v for k, v in props.iteritems() if k not in subprops)
        self.names_cache[cls] = names, all_names
        return names

    @property
    def widget(self):
        return urwid.AttrWrap(urwid.Text('properties'),  'grayed')

    def make_child(self, item):
        return PropertyWalker(self.obj, item)


class PropertyWalker(TreeWalker):
    expanded = False

    def __init__(self, obj, name):
        super(PropertyWalker, self).__init__(obj)
        self.name = name
        self.prop = getattr(type(obj), name)

    @property
    def list(self):
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
        widget = urwid.Text([self.name, ' ', str(value)])
        effect = self.prop.get_effect(self.obj)
        try:
            is_constant = effect.is_constant
        except AttributeError:
            is_constant = False
        if is_constant:
            widget = urwid.AttrWrap(widget, 'grayed')
        return widget

    def make_child(self, item):
        return EffectWalker(item)


class EffectWalker(PropertiesWalker):
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
    main = Main(clock, layer)
    loop = urwid.MainLoop(main, palette=palette)
    loop.set_alarm_in(1 / 30, main.tick, None)
    window = gillcup_graphics.Window(layer, *args, **kwargs)
    loop.run()

if __name__ == '__main__':
    import random
    layer = gillcup_graphics.Layer(name='Base')
    clock = gillcup_graphics.RealtimeClock()
    r = random.random
    def make_random_rect(parent=layer, d=0):
        rect = gillcup_graphics.Rectangle(parent, relative_anchor=(0.5, 0.5),
            size=(r() * 0.1, r() * 0.1), rotation=r() * 360,
            position=(r() + d, r() + d), color=(r(), r(), r()))
        clock.schedule(gillcup.Animation(rect, 'rotation', r() * 180 - 90,
            time=1, timing='infinite', dynamic=True))
        return rect
    for i in range(10):
        make_random_rect()
    rect = gillcup_graphics.Rectangle(layer, name='Big rect',
        relative_anchor=(0.5, 0.5), position=(0.5, 0.5), size=(0.5, 0.5))
    rotating_layer = gillcup_graphics.Layer(layer, name='Rotating layer',
        anchor=(0.5, 0.5), position=(0.5, 0.5), scale=1.5)
    clock.schedule(gillcup.Animation(rect, 'rotation', 180, time=10,
        timing='infinite'))
    clock.schedule(gillcup.Animation(rotating_layer, 'rotation', -180, time=10,
        timing='infinite'))
    def next_waypoint():
        clock.schedule(next_waypoint, 1)
        clock.schedule(gillcup.Animation(rect,
            'position', r(), r(), time=5, easing='quadratic'))
        new_rect = make_random_rect(rotating_layer, -0.5)
        new_rect.opacity = 0
        clock.schedule(gillcup.Animation(new_rect, 'opacity', 1, time=1))
        new_rect.name = 'R{0}'.format(clock.time)
    def delete_random_rect():
        if not rotating_layer.children:
            return
        victim = random.choice(rotating_layer.children)
        clock.schedule(gillcup.Animation(victim, 'opacity', 0, time=1 + r()) +
            victim.die)
    def next_deletion():
        clock.schedule(next_deletion, 1 + r())
        delete_random_rect()
    def next_masskill():
        clock.schedule(next_masskill, 10)
        for c in rotating_layer.children[5:]:
            delete_random_rect()
    next_waypoint()
    next_deletion()
    next_masskill()

    run(clock, layer, resizable=True)
