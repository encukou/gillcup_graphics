#!/usr/bin/env python
# Encoding: UTF-8

from __future__ import division, unicode_literals

import urwid
import pyglet
import gillcup_graphics
import gillcup
import fractions

palette = {}


class Main(urwid.Frame):
    _selectable = True

    def __init__(self, clock, layer):
        self.layer = layer
        self.clock = clock
        self.clock_column = TimeColumn(clock)
        self.columns = urwid.Columns([
                self.clock_column,
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
        clock.events.sort()
        if pos < 0:
            return urwid.Text(''), -1
        if pos > len(self.clock.events) - 1:
            return urwid.Text(''), len(self.clock.events)
        event = clock.events[pos]
        size = len('{0:.3f}'.format(clock.events[-1].time))
        text = '{0:{1}.3f} {2}'.format(
            event.time, size, event.action)
        return urwid.Text(text), pos

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
        self.clock_header.set_text('{0:.3f}\n{1}'.format(
            self.clock.time, speed_str))
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


def run(clock, layer, *args, **kwargs):
    main = Main(clock, layer)
    loop = urwid.MainLoop(main, palette)
    loop.set_alarm_in(1 / 30, main.tick, None)
    window = gillcup_graphics.Window(layer, *args, **kwargs)
    loop.run()

if __name__ == '__main__':
    layer = gillcup_graphics.Layer()
    rect = gillcup_graphics.Rectangle(layer, relative_anchor=(0.5, 0.5),
        position=(0.5, 0.5), size=(0.5, 0.5))
    clock = gillcup_graphics.RealtimeClock()
    clock.schedule(gillcup.Animation(rect, 'rotation', 180, time=10,
        timing='infinite'))
    import random
    for i in xrange(1000):
        clock.schedule(gillcup.Animation(rect, 'position',
            random.random(), random.random(), time=5, easing='quadratic'),
            dt=i/3)

    run(clock, layer, resizable=True)
