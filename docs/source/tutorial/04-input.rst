Input
=====

Now, let us handle users' input.
We'll start with mouse handling.

To handle mouse input, you need to define event handlers in your
:class:`~gillcup_graphics.GraphicsObject`.
These are methods called ``on_pointer_motion``, ``on_pointer_press``, and so
on.
Each one is called with a pointer (cursor) identifier, coordinates, and
possibly other keyword arguments.
The ``pointer`` identifier is currently always the string ``'mouse'``.
If you hook your program up to a different input system than a traditional
mouse-based computer, such as a multi-touch screen, you can use different
pointer identifiers to differentiate between different pointers [1]_.

The coordinates are more interesting.
These come in three arguments, ``x, y, z`` [2]_, and represent the position
of the pointer in the object's own local coordinates.

The keyword arguments vary depending on the event type.
For example, press and drag events will be called with a “button” argument.
The methods need to accept any additional arguments that might be passed to
them (for example, if someone connects Gillcup Graphics to a tablet, you
might start getting pressure/tilt information in the events).

For ``motion`` and ``press`` events, the handler can return a true value to
“claim” the event.
Once claimed, events don't propagate to any objects that might be below the
claimer.
For ``press`` events, the claimer will also exclusively get subsequent ``drag``
and ``release`` events.

Enough theory!
The following example is a bit less minimal than the previous ones,
but it should illustrate typical Gillcup Graphics usage better:

.. literalinclude:: ../examples/04-pointer.py

Let's take it one class at a time, this time.

The ``DemoRect`` class defines a rectangle that changes color depending on
mouse input.
In the ``on_pointer_motion`` and ``on_pointer_leave``, we keep track of which
pointers are “hovering” over.
If there are any, it changes color to cyan (or more precisely, becomes “less
red”).
When the last pointer leaves, it switches back to white (or, “full red”).
The ``on_pointer_press`` and ``on_pointer_leave`` do a similar thing with
button-press-based events, except for each pointer they also remember which
buttons are pressed.
From the time a button is pressed over the rectangle, to the time the last such
button is released, the square is “less green”.
This nicely illustrates the dragging concept: even if you drag your mouse out
of a rectangle, it still counts as dragging that rectangle, and the “release”
events will fire even if the mouse is outside at that time.

The ``DraggableRect`` uses ``press``, ``drag``, and ``release`` events to
implement an object that can be dragged around: it remembers where, relative
to itself, the drag started, and when dragged, moves so that the pointer is
at the same place (again, relative to the DraggableRect).

Finally, the ``DemoLayer`` is just a container for a hundred instances of
``DemoRect`` and a ``DraggableRect``. One ``DemoRect`` is rotated and
discolored to show what happens with transformations and overlapping.


.. [1] Of course, you'd need to do such hooking up manually, by calling
    :meth:`~gillcup_graphics.GraphicsObject.pointer_event` of your root layer.
.. [2] The ``z`` coordinate will generally be zero.
