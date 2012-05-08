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

    Subclassable methods:

        .. automethod:: gillcup_graphics.GraphicsObject.is_hidden
        .. automethod:: gillcup_graphics.GraphicsObject.change_matrix
        .. automethod:: gillcup_graphics.GraphicsObject.die

.. autoclass:: gillcup_graphics.Layer

    .. automethod:: gillcup_graphics.Layer.draw

.. autoclass:: gillcup_graphics.Rectangle

    Animated Properties:

        .. autoattribute:: gillcup_graphics.Rectangle.color
        .. autoattribute:: gillcup_graphics.Rectangle.opacity

.. autoclass:: gillcup_graphics.Sprite

    Animated Properties:

        .. autoattribute:: gillcup_graphics.Sprite.color
        .. autoattribute:: gillcup_graphics.Sprite.opacity

.. autoclass:: gillcup_graphics.Text

    .. autoattribute:: gillcup_graphics.Text.size

    Animated Properties:

        .. autoattribute:: gillcup_graphics.Text.color
        .. autoattribute:: gillcup_graphics.Text.opacity
        .. autoattribute:: gillcup_graphics.Text.font_size
        .. autoattribute:: gillcup_graphics.Text.characters_displayed
