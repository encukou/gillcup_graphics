#!/usr/bin/env python
# Encoding: UTF-8

from __future__ import division, unicode_literals

import urwid
import pyglet
import fractions
import weakref
import collections

import gillcup_graphics
import gillcup

palette = {}


class Main(urwid.Frame):
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
        pyglet.clock.tick()

        for window in pyglet.app.windows:
            window.switch_to()
            window.dispatch_events()
            window.dispatch_event('on_draw')
            window.flip()

        loop.set_alarm_in(1 / 30, self.tick, None)

    def keypress(self, size, key):
        if key == ' ':
            self.clock_column.toggle_pause()
        elif key in '-_':
            self.clock_column.speed_down()
        elif key in '+=':
            self.clock_column.speed_up()
        elif key in '0':
            self.clock_column.speed_normal()
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
        if 0 <= pos < len(self.clock.events) - 1:
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
        self.clock_header.set_text('{0:.3f} ({1:.1f} fps)\n{2}'.format(
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

    def update_clock_speed(self):
        if self.paused:
            self.clock.speed = 0
        else:
            self.clock.speed = self.clock_speed
        self._set_text()


class TreeWalker(urwid.ListWalker):
    list = ()

    def __init__(self, obj=None):
        super(TreeWalker, self).__init__()
        self.position = []
        self.cache = weakref.WeakKeyDictionary()
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
            return item.widget, position

    def get_focus(self):
        return self.get_at(self.position)

    def next_position(self, position):
        if position:
            index = position[0]
            pos = self[index].next_position(position[1:])
            if pos is not None:
                return [index] + pos
            elif index + 1 < len(self.list):
                return [index + 1]
            else:
                return None
        elif len(self.list):
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
        if len(self.list):
            last = len(self.list) - 1
            return [last] + self[last].last_position()
        else:
            return []

    def get_next(self, position):
        return self.get_at(self.next_position(position))

    def get_prev(self, position):
        return self.get_at(self.prev_position(position))

    def set_focus(self, position):
        self.position = position
        self._modified()

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
        self.list = (
                ChildrenWalker(obj),
            )
        super(GraphicsObjectWalker, self).__init__(obj)

    @property
    def widget(self):
        obj = self.obj
        if obj.name:
            name_part = obj.name + ' '
        else:
            name_part = ''
        text = [name_part, '({0})'.format(type(obj).__name__)]
        return urwid.Text(text, wrap='clip')

class ChildrenWalker(TreeWalker):
    @property
    def list(self):
        return self.obj.children

    @property
    def widget(self):
        return urwid.Text('[children]', wrap='clip')

    def make_child(self, item):
        return GraphicsObjectWalker(item)


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
    loop = urwid.MainLoop(main, palette)
    loop.set_alarm_in(1 / 30, main.tick, None)
    window = gillcup_graphics.Window(layer, *args, **kwargs)
    loop.run()

if __name__ == '__main__':
    import random
    layer = gillcup_graphics.Layer(name='Base')
    clock = gillcup_graphics.RealtimeClock()
    for i in range(10):
        r = random.random
        rect = gillcup_graphics.Rectangle(layer, relative_anchor=(0.5, 0.5),
            size=(r() * 0.1, r() * 0.1), rotation=r() * 360,
            position=(r(), r()), color=(r(), r(), r()))
        clock.schedule(gillcup.Animation(rect, 'rotation', 180,
            time=r() * 10 + 1, timing='infinite'))
    rect = gillcup_graphics.Rectangle(layer, relative_anchor=(0.5, 0.5),
        position=(0.5, 0.5), size=(0.5, 0.5))
    clock.schedule(gillcup.Animation(rect, 'rotation', 180, time=10,
        timing='infinite'))
    def schedule_next_waypoint():
        clock.schedule(gillcup.Animation(rect, 'position',
            random.random(), random.random(), time=5, easing='quadratic'))
        clock.schedule(schedule_next_waypoint, 1)
    schedule_next_waypoint()

    run(clock, layer, resizable=True)
