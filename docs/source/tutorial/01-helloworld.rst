Hello, World!
=============

.. note::

    This is not an introduction page for dummies.

    Despite the name, this page covers lots of info.
    It also introduces some problems that `you` (the programmer, not the
    library), will be expected to solve in your applications, and gives
    an example of how to solve them.
    In exchange for what looks like boilerplate code now, you get the freedom
    to later solve the problems in other ways.
    Ways which which are more appropriate in your case.
    Ways which, hopefully, let you do more than the library's author imagined.

    You'll have to understand what you're doing, and have an idea of what
    the library is doing for you.
    If that rubs you the wrong way, you should pick a different library.

To greet the planet, type this into your favorite editor ad run it::

    from gillcup_graphics import Layer, Text, Window, run

    root_layer = Layer()

    hi_world = Text(root_layer, 'Hello, World!',
            position=(0.5, 0.5),
            relative_anchor=(0.5, 0),
            scale=(0.001, 0.001),
        )

    Window(root_layer, width=400, height=400)

    run()

It's quite a lot to take in at once, so let's go through it one line at a time.

Obviously, you will need to import some objects first. For our first example
we'll only need four::

    from gillcup_graphics import Layer, Text, Window, run

Once that's done, we'll create a :class:`~gillcup_graphics.Layer`::

    root_layer = Layer()

You probably know about the kind of layers you can find in modern painting
applications: potentially semi-transparent “sheets” stacked atop
one another, with layers further down showing wherever the higher layers
are transparent.

Our kind of layers is a somewhat different take on that sheets idea.
They are not just stacked, but arranged in trees:
each layer can have one or more children, either other layers or different
objects.
When you move, rotate, or resize a layer, all its children are moved, rotated
or resized with it.
Layers themselves are completely transparent; the actual drawing is done by the
leaves of the scene tree.

The layer at the root of a scene tree – here, ``root_layer`` – is typically the
only graphics object that doesn't have a parent.
For the others, we specify a parent as the first argument when creating them::

    hi_world = Text(root_layer, 'Hello, World!',

Here, we're creating a :class:`~gillcup_graphics.Text` object in our
``root_layer``.
We're also passing a certain well-loved string for the Text object to draw.
(Note that the assignment is actually unnecessary. The text gets attached to
the layer just by having a parent specified; a reference doesn't need to be
kept around.)

Unfortunately, just that won't do.
We also need to specify where we want the text to be drawn.
Let's put it in the middle::

            position=(0.5, 0.5),

This brings us to the concept of coordinates and sizing.
Since we did not specify a :attr:`~gillcup_graphics.GraphicsObject.size` for
``root_layer``, it has a default size of 1×1 unit.
Later, when we display it, it will be stretched (`scaled`) to cover the entire
window (in our case, 400×400 pixels).
However, regardless of the scaling, the children of the layer deal with
a unit square, and (0.5, 0.5) is right in the middle of that.

There's one more problem: as customary in OpenGL (and Pyglet (and math)), the
origin of the coordinate system is in the lower-left corner.
The ``position`` argument moves the origin to the specified point.
So if we just set the ``position`` to ``(0.5, 0.5)``, our text wouldn't be
centered at all!

The solution to this problem is to set the ``anchor`` property.
The anchor specifies the origin of the coordinate system, in whatever units
the object itself uses.
Just what we need? Well, anmost.
The catch is in the units.
Unlike Layers, a Text's size is not 1×1 units, instead,
it's the pixel size of the underlying glyph textures.
In our case, it should be something in the ballpark of 600×100, although
can't say for sure, because I don't know what font Pyglet uses on your
system by default.
So, to really center the object, we'd either need to say something like
``anchor = (300, 50)``, and ignore the inaccuracy, or create the object,
get its size, and set the anchor to half or that.

There's a more elegant approach::

            relative_anchor=(0.5, 0),

``relative_anchor`` maps the given coordinates from an unit square to the
object's size and sets ``anchor`` to the result.
So, with ``(0.5, 0)``, anchor will always be in the bottom center of the object
(even if the text is later resized).
This is done with a bit of :class:`magic <gillcup:gillcup.Effect>` that will
be dispelled later: with Gillcup, it's not that hard to code such dynamic
properties yourself.

The astute reader has no doubt noticed that we did not align the text to the
center of its bounding rectangle, ``(0.5, 0.5)``, but to the bottom center,
``(0.5, 0)``.
This is purely for æsthetic reasons: the composition tends to look better when
a centered object is a bit above the actual center.

Now that we know something about our objects' geometry, the last argument
to the text should start to make sense::

            scale=(0.001, 0.001),
        )

If we tried to put a roughly 600×100 text in a 1×1 window, we'd see,
in the best case, a small part of a giant white blob.
More probably, we'd see nothing, because we'd hit the space between
the letters.

To bring the text back to scale, we shrink it to a thousandth of its original
size, making it roughly 0.6×0.1.
That will fit in a 1×1 square easily, leaving nice wide margins around.

And now that our scene is constructed, we can worry about displaying it::

    Window(root_layer, width=400, height=400)

This creates a special Pyglet window that redirects its draw events to the
``root_layer``. [1]_

And now the last step::

    run()

The run function simply runs a Pyglet main loop, which handles draw events
and window close events and various other kinds of events that we haven't
taken advantage of just yet.

Finally, you get to see our piece of text (and notice that it doesn't really
look all that impressive [2]_).
But, at least you understand it now!
Later in the tutorial you'll learn about animations, input handling,
and other objects to draw (such as :class:`sprites <gillcup_graphics.Sprite>`).
There's not that much left until your first Gillcup game!



.. [1] It also redirects other events, such as mouse and resize ones.
.. [2] In a real application, you'll probably want to load a known font, and
    adjust all the sizes to be pixel-perfect.
    This requires some Pyglet-fu.
