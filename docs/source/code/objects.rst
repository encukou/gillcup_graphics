gillcup_graphics.objects
========================

.. automodule:: gillcup_graphics.objects

.. autoclass:: gillcup_graphics.GraphicsObject

    .. automethod:: gillcup_graphics.GraphicsObject.draw
    .. automethod:: gillcup_graphics.GraphicsObject.reparent

    Animated Properties:

        .. autoattribute:: gillcup_graphics.GraphicsObject.position
        .. autoattribute:: gillcup_graphics.GraphicsObject.anchor
        .. autoattribute:: gillcup_graphics.GraphicsObject.relative_anchor
        .. autoattribute:: gillcup_graphics.GraphicsObject.scale
        .. autoattribute:: gillcup_graphics.GraphicsObject.size
        .. autoattribute:: gillcup_graphics.GraphicsObject.rotation

    Event handlers:

        .. automethod:: gillcup_graphics.GraphicsObject.pointer_event
        .. automethod:: gillcup_graphics.GraphicsObject.on_pointer_motion
        .. automethod:: gillcup_graphics.GraphicsObject.on_pointer_leave
        .. automethod:: gillcup_graphics.GraphicsObject.on_pointer_press
        .. automethod:: gillcup_graphics.GraphicsObject.on_pointer_drag
        .. automethod:: gillcup_graphics.GraphicsObject.on_pointer_release

    Other subclassable methods:

        .. automethod:: gillcup_graphics.GraphicsObject.is_hidden
        .. automethod:: gillcup_graphics.GraphicsObject.hit_test
        .. automethod:: gillcup_graphics.GraphicsObject.transform
        .. automethod:: gillcup_graphics.GraphicsObject.die

    Internal methods:

        .. automethod:: gillcup_graphics.GraphicsObject.set_animated_properties
        .. automethod:: gillcup_graphics.GraphicsObject.die

.. autoclass:: gillcup_graphics.Layer

    .. automethod:: gillcup_graphics.Layer.draw

.. autoclass:: gillcup_graphics.DecorationLayer

.. autoclass:: gillcup_graphics.Rectangle

    .. automethod:: gillcup_graphics.Rectangle.hit_test

    Animated Properties:

        .. autoattribute:: gillcup_graphics.Rectangle.color
        .. autoattribute:: gillcup_graphics.Rectangle.opacity

.. autoclass:: gillcup_graphics.Sprite

    .. automethod:: gillcup_graphics.Sprite.hit_test

    Animated Properties:

        .. autoattribute:: gillcup_graphics.Sprite.color
        .. autoattribute:: gillcup_graphics.Sprite.opacity

.. autoclass:: gillcup_graphics.Text

    .. automethod:: gillcup_graphics.Text.hit_test

    .. autoattribute:: gillcup_graphics.Text.size

    Animated Properties:

        .. autoattribute:: gillcup_graphics.Text.color
        .. autoattribute:: gillcup_graphics.Text.opacity
        .. autoattribute:: gillcup_graphics.Text.font_size
        .. autoattribute:: gillcup_graphics.Text.characters_displayed
