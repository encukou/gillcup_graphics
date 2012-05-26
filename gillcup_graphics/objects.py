# Encoding: UTF-8
"""Drawable objects

This module provides basic objects you can draw and animate.

Perhaps the most important of these is the :class:`Layer`, which does not have
a graphical representation by itself, but can contain other objects, such as a
:class:`~gillcup_graphics.Rectangle`, :class:`~gillcup_graphics.Sprite` or
another :class:`~gillcup_graphics.Layer`.
Graphics objects are thus arranged in a scene tree.
The tree is rooted at a parent-less Layer [#f1]_, which will usually be shown
in a :class:`~gillcup_graphics.Window`.

Each object has a lot of AnimatedProperties that control its position on the
screen (relative to its parent), and properties like color and opacity.

The objects are compatible with 3D transformations, but anything outside the
`z=0` plane needs custom OpenGL camera setup.
Refer to Pyglet documentation for details.

.. [#f1] To be precise, the root may be any object. It's just that non-Layers
    aren't terribly useful here.
"""

from __future__ import division, unicode_literals

import sys
import re
import collections

import pyglet
from pyglet import gl

import gillcup
from gillcup import properties
from gillcup.effect import Effect

color_property = gillcup.TupleProperty(1, 1, 1,
    docstring="""Color or tint of the object

    The individual components are in the ``red``, ``green``, ``blue``
    attributes.""")

opacity_property = gillcup.AnimatedProperty(1,
        docstring="""Opacity of the object""")


class GraphicsObject(object):
    """Base class for gillcup_graphics scene objects

    :param parent: The parent :class:`Layer` in the scene tree
    :param to_back: If false (default), the object is inserted at the end of
        the parent's children list, and thus is drawn after (in front of) its
        existing siblings.
        If true, it will be is drawn before (behind) them.
    :param name: An optional name of the object. It is stored in the ``name``
        attribute.
    :param kwargs: Any animated property (including those from subclasses)
        can be initialized by passing a value as a keyword argument to
        ``__init__``.
    """
    def __init__(self,
            parent=None,
            to_back=False,
            name=None,
            **kwargs):
        super(GraphicsObject, self).__init__()
        self.parent = None
        self.reparent(parent, to_back)
        self.name = name
        self.children = ()
        self.dead = False
        if 'anchor' not in kwargs:
            RelativeAnchor(self).apply_to(self, 'anchor')
        self.set_animated_properties(kwargs)

    x, y, z = position = properties.VectorProperty(3,
        docstring="""The object's position in space

        This is an offset between the parent's anchor and this object's own
        anchor, in the parent's coordinates.

        The individual components are in the ``x``, ``y``, ``z``
        attributes.""")
    anchor_x, anchor_y, anchor_z = anchor = properties.VectorProperty(3,
        docstring="""A point that represents this object for positioning.

        The individual components are in the ``anchor_x``, ``anchor_y``,
        ``anchor_z`` attributes.""")
    scale_x, scale_y, scale_z = scale = properties.ScaleProperty(3,
        docstring="""The object's scale.

        The individual components are in the ``scale_x``, ``scale_y``,
        ``scale_z`` attributes.""")
    width, height = size = properties.ScaleProperty(2,
        docstring="""The object's natural size

        The individual components are in the ``width`` and ``height``
         attributes.""")
    rotation = gillcup.AnimatedProperty(0,
        docstring="""Rotation about the object's anchor""")
    relative_anchor = properties.VectorProperty(3,
        docstring="""Anchor of the object relative to the object's size

        When ``relative_anchor`` is (1, 1), the ``anchor`` is in the
        object's upper right corner. When ``relative_anchor`` is (0.5, 0.5),
        ``anchor`` will me in the middle.

        This property is only effective if ``anchor`` is not set by other
        means.

        The individual components are in the ``relative_anchor_x``,
        ``relative_anchor_y``, ``relative_anchor_z`` attributes.""")
    relative_anchor_x, relative_anchor_y, relative_anchor_z = relative_anchor

    def set_animated_properties(self, kwargs):
        """Initializes animated properties with keyword arguments"""
        unknown = []
        for name, value in kwargs.items():
            try:
                prop = getattr(type(self), name)
            except AttributeError:
                unknown.append(name)
            else:
                if isinstance(prop, gillcup.AnimatedProperty):
                    setattr(self, name, value)
                else:
                    unknown.append(name)
        if unknown:
            raise TypeError('Unknown keyword arguments: %s' %
                    ', '.join(unknown))

    def is_hidden(self):
        """Return true if this object (and any children) shouldn't be shown"""
        if getattr(self, 'opacity', 1) <= 0:
            return False
        return self.dead or not any(self.scale)

    def do_draw(self, transformation, **kwargs):
        """Draw this object

        This method sets up the transformation matrix and calls draw().
        If this method returns false, the object is removed from its parent.

        Subclasses will usually want to override draw(), not this method.
        """
        # XXX: Make sure tree is never deeper than 32
        if self.dead:
            return False
        elif self.is_hidden():
            return True
        with transformation.state:
            self.change_matrix(transformation)
            self.draw(transformation=transformation, **kwargs)
        return True

    def draw(self, **kwargs):
        """Draw this object. Overridden in subclasses.

        :param transformation: A
            :class:`~gillcup_graphics.transformation.GlTransformation` object
            controlling the current OpenGL matrix.
        :param window: A :class:`~gillcup_graphics.Window` for which the
            drawing is done.

        Additional keyword arguments might be present. Unknown ones should
        be passed to child objects unchanged.
        """
        pass

    def change_matrix(self, transformation):
        """Set up the transformation matrix for object

        :param transformation: The
            :class:`~gillcup_graphics.transformation.BaseTransformation` object
            to modify in-place.

        No :meth:`~gillcup_graphics.transformation.BaseTransformation.push`
        or :meth:`~gillcup_graphics.transformation.BaseTransformation.pull`
        calls should be made, only transformations.
        """
        transformation.translate(*self.position)
        transformation.rotate(self.rotation, 0, 0, 1)
        transformation.scale(*self.scale)
        transformation.translate(*(-x for x in self.anchor))

    def hit_test(self, x, y, z):
        """Perform a hit test on this object

        Return false if the given point (in local coordinates) is "outside" the
        object.
        """
        return True

    def die(self):
        """Destroy this object

        Sets up to detach from the parent on the next frame, and calls die()
        on all children.
        """
        self.dead = True
        self.parent = None
        for child in self.children:
            if child.parent is self:
                child.die()

    def reparent(self, new_parent, to_back=False):
        """Set a new parent

        Remove this object from the current parent (if there is one) and
        attech to a new one (if new_parent is not ``None``.
        The `to_back` argument is the same as for :meth:`__init__`.

        Beware that reparenting may throw off the mouse tracking mechanism.
        Specifically, 'leave' and after-drag 'release' events might not fire.
        Mouse-aware objects should run their leave/release handlers before
        calling reparent().
        """
        assert new_parent is not self
        if self.parent:
            self.parent.children = [
                    c for c in self.parent.children if c is not self
                ]
            self.parent = None
        if new_parent:
            if to_back:
                new_parent.children.insert(0, self)
            else:
                new_parent.children.append(self)
            self.parent = new_parent

    def pointer_event(self, type, pointer, x, y, z, **kwargs):
        """Handle a pointer (mouse) event, return true if it as handled

        :param type: Can be 'motion', 'press', 'release', 'leave', 'drag',
        or 'scroll'

        For 'press', return True (i.e. the bool value, not just any true-ish
        object) to "claim" the click/drag operation. Only the "claiming" object
        will get subsequent drag & release events.

        For 'motion', return True  stop the event from propegating to items
        underneath. (This won't prevent later "leave" events)
        """
        pass

    def keyboard_event(self, type, keyboard, **kwargs):
        """Handle a keyboard event, return true if it as handled"""
        pass


class RelativeAnchor(Effect):
    """Put on an ``anchor`` property to make it respect relative_anchor"""
    def __init__(self, obj):
        super(RelativeAnchor, self).__init__()
        self.object = obj

    @property
    def value(self):
        """Calculate the value"""
        obj = self.object
        return (obj.width * obj.relative_anchor_x,
            obj.height * obj.relative_anchor_y)


class Layer(GraphicsObject):
    """A container for GraphicsObjects

    The Layer is unique in that it can contain child objects.

    Init arguments are the same as for
    :class:`~gillcup_graphics.GraphicsObject`.
    """

    def __init__(self, parent=None, **kwargs):
        super(Layer, self).__init__(parent, **kwargs)
        self.children = []
        self.hovered_children = dict()
        self.dragging_children = collections.defaultdict(dict)

    def draw(self, transformation, **kwargs):
        """Draw all of the layer's children"""
        transformation.translate(*self.anchor)
        self.children = [
                c for c in self.children if c.do_draw(
                        transformation=transformation,
                        **kwargs
                    )
            ]


    def pointer_event(self, kind, pointer, x, y, z, **kwargs):
        toplevel = 'global_point' not in kwargs
        if toplevel:
            global_point = kwargs['global_point'] = x, y, z
        else:
            global_point = kwargs['global_point']
        def _children_for_ptr(children, x, y, z):
            # CAREFUL! Yield inside a transformation.state context!
            for child in reversed(children):
                with transformation.state:
                    child.change_matrix(transformation)
                    try:
                        point = transformation.point
                    except ValueError:
                        yield child, (-1, -1, -1), None
                    else:
                        hit = child.hit_test(*point)
                        yield child, point, hit

        transformation = kwargs['transformation']
        if kind == 'leave':
            children = list(self.hovered_children.get(pointer, ()))
            for child, point, hit in _children_for_ptr(children, x, y, z):
                child.pointer_event('leave', pointer, *point, **kwargs)
            self.hovered_children.pop(pointer, None)
        elif kind == 'motion':
            if toplevel:
                reg = self.dragging_children.get(pointer, {})
                for button, child in reg.iteritems():
                    if child in self.children:
                        with transformation.state:
                            child.change_matrix(transformation)
                            point = transformation.point
                            child.pointer_event('drag', pointer, *point,
                                button=button, **kwargs)
            new_hovered_children = set()
            retval = None
            for child, point, hit in _children_for_ptr(self.children, x, y, z):
                if hit:
                    retval = child.pointer_event('motion', pointer, *point,
                        **kwargs)
                    new_hovered_children.add(child)
                    if retval:
                        break
            hovered = self.hovered_children.get(pointer, set())
            for child in hovered - new_hovered_children:
                child.pointer_event('leave', pointer, *point, **kwargs)
            self.hovered_children[pointer] = new_hovered_children
            return retval
        elif kind == 'press':
            button = kwargs['button']
            for child, point, hit in _children_for_ptr(self.children, x, y, z):
                if hit:
                    ret = child.pointer_event(kind, pointer, *point, **kwargs)
                    if ret:
                        self.dragging_children[pointer][button] = child
                        return ret
        elif kind == 'release':
            button = kwargs['button']
            try:
                child = self.dragging_children[pointer][button]
            except KeyError:
                pass
            else:
                if child in self.children:
                    with transformation.state:
                        child.change_matrix(transformation)
                        point = transformation.point
                        child.pointer_event(kind, pointer, *point, **kwargs)
                del self.dragging_children[pointer][button]
                if not self.dragging_children[pointer]:
                    del self.dragging_children[pointer]


class DecorationLayer(Layer):
    """A Layer that does not respond to hit tests

    Objects in this layer will not be interactive.
    """
    def do_hit_test(self, transformation, **kwargs):
        return ()

    def pointer_event(*_ignore, **_everything):
        pass


class Rectangle(GraphicsObject):
    """A box of color"""

    color = red, green, blue = color_property
    opacity = opacity_property

    vertices = (gl.GLfloat * 8)(0, 0, 1, 0, 0, 1, 1, 1)

    def draw(self, transformation, **kwargs):
        transformation.scale(self.width, self.height, 1)
        color = self.color + (self.opacity, )
        gl.glColor4fv((gl.GLfloat * 4)(*color))
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, self.vertices)
        gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)

    def hit_test(self, x, y, z):
        """Perform a hit test on the rectangle"""
        return 0 <= x < self.width and 0 <= y < self.height


class Sprite(GraphicsObject):
    """An image

    :param texture: A Pyglet image to show in this sprite.
        You can use the :meth:`pyglet.image.load` to obtain one.

    Other init arguments are the same as for
    :class:`~gillcup_graphics.GraphicsObject`.
    """

    color = red, green, blue = color_property
    opacity = opacity_property

    def __init__(self, parent, texture, **kwargs):
        self.sprite = pyglet.sprite.Sprite(texture.get_texture())
        kwargs.setdefault('size', (self.sprite.width, self.sprite.height))
        super(Sprite, self).__init__(parent, **kwargs)

    def draw(self, **kwargs):
        self.sprite.opacity = self.opacity * 255
        self.sprite.color = tuple(int(c * 255) for c in self.color)
        gl.glScalef(
                self.width / self.sprite.width,
                self.height / self.sprite.height,
                1,
            )
        self.sprite.draw()

    def hit_test(self, x, y, z):
        """Perform a hit test on this object. Uses the sprite size.

        Does not take e.g. alpha into account"""
        return 0 <= x < self.width and 0 <= y < self.height


def sanitize_text(string):
    """Sanitize a string for use in a name"""
    def _sanitize_char(match):
        group = match.group()
        if group == '\n':
            return r'↵'
        elif group == '\x7f':
            return '\N{SYMBOL FOR DELETE}'
        else:
            return unichr(0x2400 + ord(match.group()))
    return re.sub(r'[\0-\x1f]', _sanitize_char, string)


class Text(GraphicsObject):
    """A text label

    :param text: A string to display n this label
    :param font_name: Name of the font to use. See Pyglet documentation for
        more info on using fonts.

    Other init arguments are the same as for
    :class:`~gillcup_graphics.GraphicsObject`.

    .. note::

        The API regarding font size is experimental.
    """
    def __init__(self, parent, text, font_name=None, **kwargs):
        super(Text, self).__init__(parent, **kwargs)
        self.text = text
        self.label = pyglet.text.Label(
                text,
                font_name=font_name,
                font_size=self.font_size,
            )
        self.font_name = font_name

    color = red, green, blue = color_property
    opacity = opacity_property
    font_size = gillcup.AnimatedProperty(72,
        docstring="The size of the font")
    characters_displayed = gillcup.AnimatedProperty(sys.maxint,
        docstring="The maximum number of characters displayed")

    @property
    def font_name(self):
        """Name of the font to use for this label"""
        return self.label.font_name

    @font_name.setter
    def font_name(self, new_font_name):
        """Name of the font to use for this label

        Refer to Pyglet docs for info on font loading.
        """
        self.label.font_name = new_font_name

    def setup(self):
        """Assign the properties to the underlying Pyglet label"""
        if self.label.font_size != self.font_size:
            self.label.font_size = self.font_size

    def draw(self, **kwargs):
        self.setup()
        label = self.label
        color = self.color + (self.opacity, )
        label.color = [int(a * 255) for a in color]
        displayed_text = self.text[:int(self.characters_displayed)]
        if label.text != displayed_text:
            label.text = displayed_text
        label.draw()

    @property
    def name(self):
        """If name is not given explicitly, use the text itself"""
        if self._name is None:
            return '"{0}"'.format(sanitize_text(self.text))
        else:
            return self._name

    @name.setter
    def name(self, new_name):
        """Set the name"""
        self._name = new_name  # pylint: disable=W0201

    @property
    def size(self):
        """The natural size of the text

        This property is not animated, and cannot be changed.

        Returns the size of the entire text, i.e. doesn't take
        ``characters_displayed`` into account.

        The ``width`` and ``height`` attributes contain the size's individual
        components.
        """
        self.setup()
        label = self.label
        if label.text != self.text:
            label.text = self.text
        return (label.content_width, label.content_height)

    @property
    def height(self):
        """Natural height of the text

        See `size`"""
        return self.size[1]

    @property
    def width(self):
        """Natural height of the text

        See `size`"""
        return self.size[0]

    def hit_test(self, x, y, z):
        """Perform a hit test on this object. Uses the bounding rectangle."""
        return 0 <= x < self.width and 0 <= y < self.height
