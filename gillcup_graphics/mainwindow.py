"""Utilities for interfacing gillcup_graphics with the rest of the world

"""

from __future__ import division

import pyglet
from pyglet import gl

import gillcup
from gillcup_graphics.transformation import (
    GlTransformation, PointTransformation)


run = pyglet.app.run


class Window(pyglet.window.Window):  # pylint: disable=W0223
    """A main window

    A convenience subclass of pyglet.window.Window that shows a
    :class:`~gillcup_graphics.Layer`

    :param layer: The layer to show. Its
        :attr:`~gillcup_graphics.GraphicsObject.scale` will be automatically
        adjusted to fit the window.

    Other arguments are passed to Pyglet's window constructor.
    """
    def __init__(self, layer, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.layer = layer
        self.on_resize(self.width, self.height)

    def manual_draw(self):
        """Draw the contents outside of the main loop"""
        self.switch_to()
        self.on_draw()
        self.flip()

    # pylint: disable=W0221
    def on_draw(self):
        gl.glClearColor(0, 0, 0, 0)
        self.clear()
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glViewport(0, 0, self.width, self.height)
        transformation = GlTransformation()
        transformation.reset()
        self.layer.do_draw(window=self, transformation=transformation)

    # pylint: disable=W0221
    def on_resize(self, width, height):
        super(Window, self).on_resize(width, height)
        layer = self.layer
        layer.scale = width / layer.width, height / layer.height, 1

    # pylint: disable=W0221
    def on_mouse_motion(self, x, y, dx, dy):
        self.pointer_event('motion', 'main', x, y, dx=dx, dy=dy)

    # pylint: disable=W0221
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.pointer_event('motion', 'main', x, y, dx=dx, dy=dy,
            buttons=buttons, modifiers=modifiers)

    # pylint: disable=W0221
    def on_mouse_press(self, x, y, button, modifiers):
        self.pointer_event('press', 'main', x, y,
            button=button, modifiers=modifiers)

    # pylint: disable=W0221
    def on_mouse_release(self, x, y, button, modifiers):
        self.pointer_event('release', 'main', x, y,
            button=button, modifiers=modifiers)

    # pylint: disable=W0221
    def on_mouse_leave(self, x, y):
        self.pointer_event('leave', 'main', x, y)

    # pylint: disable=W0221
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.pointer_event('scroll', 'main', x, y,
            scroll_x=scroll_x, scroll_y=scroll_y)

    def pointer_event(self, kind, pointer, x, y, **kwargs):
        """Fire a pointer event on the client layer"""
        transformation = PointTransformation(x, y, 0)
        layer = self.layer
        with transformation.state:
            layer.transform(transformation)
            layer.pointer_event(kind, pointer,
                transformation=transformation, **kwargs)

    # pylint: disable=W0221
    def on_key_press(self, key, modifiers):
        self.layer.keyboard_event('press', 'main',
            key=key, modifiers=modifiers)

    def on_key_release(self, key, modifiers):
        self.layer.keyboard_event('release', 'main',
            key=key, modifiers=modifiers)

    def on_text(self, text):
        try:
            # Work around a Pyglet bug
            text = text.encode('latin-1').decode('utf-8')
        except UnicodeError:
            pass
        self.layer.do_keyboard_event('type', 'main', text=text)

    def on_text_motion(self, motion):
        self.layer.do_keyboard_event('motion', 'main', motion=motion)


class RealtimeClock(gillcup.Clock):
    """A :class:`gillcup.Clock` tied to the system time

    Note that the Pyglet main loop must be running (or the Pyglet clock must
    be ticked otherwise) for this to work.
    """
    def __init__(self):
        super(RealtimeClock, self).__init__()
        pyglet.clock.schedule(self.advance)
