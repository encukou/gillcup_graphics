Animations
==========

Now that we've got the Clock basics out of the way, let's talk about
Animations: a way to smoothly change an object's attribute over time.

First, let's take a look at this piece of code (differences from the previous
page are highlighted):

.. literalinclude:: ../examples/03-animations.py
    :emphasize-lines: 2,19,21,28

Aside from a new import, the first difference is in the blink function:

.. literalinclude:: ../examples/03-animations.py
    :lines: 19

Here, instead of just changing the value, we schedule an
:class:`~gillcup.Animation` on our clock.
The Animation will smoothly change ``rect``'s ``opacity`` from its current
value to ``1`` in the interval of ``0.3`` seconds (that is, 0.3 of whatever
units of time ``clock`` uses).

The second changed line is similar – it just animates the value back to zero.

The last added line reads:

.. literalinclude:: ../examples/03-animations.py
    :lines: 28

Similar to the above, this smoothly changes the ``rotation`` from the current
value (45) to 0 in the course of 1 second.
However, due to the ``infinite`` timing, it doesn't stop there: it continues
past 0° and goes on, through -45° in the second second, -90° in the third,
and so on.
The final effect is that our square will rotate forever.

The :class:`~gillcup.Animation` class has several options and subclasses that
let you take control of exactly how the attribute is changed;
the ``infinite`` timing is just one of them.

If you wish to control an animated property in ways unrelated to a clock,
take a look in the :mod:`gillcup.effect` module.
The Effect class provides the control over an attribute; Animation is an Effect
subclass that adds time-related stuff. And chaining.


Chaining animations
-------------------

Animations offer a way to schedule an action to do after they are done.
In the following code:

.. literalinclude:: ../examples/03-chaining.py
    :emphasize-lines: 16-27

…the :meth:`~gillcup.Action.chain` method does just that:
when an Animation is done, ``chain``'s argument is scheduled on that
Animation's clock.
The argument can be another Animation, or just a regular callable.

When doing complex stuff, be aware that each Animation can only be scheduled
and run once.
If you need to do the same thing several times, you can make an Animation
factory (look at ``blink`` in the first Animation example).


Building animations
-------------------

Using the ``chain`` method can be clumsy at times.
Another way to build complex animations from the basic building blocks is
provided by the ``+`` and ``|`` operators:

.. literalinclude:: ../examples/03-building.py
    :emphasize-lines: 19-27

The operators create a larger animation, which runs its components one after
the other (``+``) or in parallel (``|``).

To create delays, you can “add” numbers to Animations.
You can also use lists (or other iterables) of animations; these work as if
all their components were “added” toghether (except iterators are evaluated
lazily).
However, be sure that you don't accidentally pass a raw number of list to
``chain`` or ``Clock.schedule``.

Since each animation can only be scheduled once, be careful to not accidentally
schedule any “parts” of a larger animation individually.

If you wish to look how this is implemented, or how to extend it in
different ways, see Gillcup's :mod:`~gillcup.actions` module.
Actions implement the concept of a chainable event; Animation (an Action
subclass) adds the changing of an object's attribute.


Processes
---------

Finally, we can schedule actions via a :class:`~gillcup.actions.Process`
generator.
This allows you to lay out an animation in a procedural manner, as if
you were writing a script for a movie.
Things that don't happen in a single instant (of Clock time) are handled
by yielding actions.
This works best for complex animations that require additional processing or
looping, but don't “branch out” too much.

.. literalinclude:: ../examples/03-process.py
    :emphasize-lines: 3,17-27

Any action [1]_ that is ``yield``-ed is scheduled on the clock, and the rest of
the process is chained to it.
Note that, again, the “infinite” animation loop is broken when its object dies.


.. [1] You can also yield numbers or lists/iterables, as with the ``+`` and
    ``|`` operators.
