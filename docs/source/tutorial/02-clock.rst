The Clock
=========

Still here? Good.


In this part of the tutorial, we'll learn about the Gillcup clock, the time
source for animations.
We'll go through the following piece of code, which draws a blinking square:

.. literalinclude:: ../examples/02-clock.py

Let's fast-forward through the beginning:

.. literalinclude:: ../examples/02-clock.py
    :lines: 1-12

The only thing that's different from the previous part of the tutorial is
that we're using a Rectangle, and the options are a bit different.
As you probably can guess, the ``rotation`` part rotates the rectangle by 45°.

Next comes the all-important line that creates a clock:

.. literalinclude:: ../examples/02-clock.py
    :lines: 14

Animations in Gillcup aren't necessarily tied to the system time.
You can use different clocks – for example, to render a movie with a fixed
frame rate, you wouldn't want to use the system time.
Or for a special effect, you might want to use a Clock that runs at a different
speed than your main Clock.
But here, we happen to be using the RealtimeClock, which is tied to the
system time, in seconds.

Now, we define a simple function that can show or hide our square:

.. literalinclude:: ../examples/02-clock.py
    :lines: 16-17

The ``hidden`` attribute sets the visibility of our Rectangle – either it's
there, or it isn't.

The final lines of our ``blink`` function look like this:

.. literalinclude:: ../examples/02-clock.py
    :lines: 19-20

Let's start with the ``schedule`` call.
The :meth:`~gillcup.Clock.schedule` method schedules a function to be
called after the given time elapses.
So, here, another instance of ``blink``, with the ``on`` argument inverted,
will be called 0.5s from the time this line runs.
That ``blink`` will schedule another one, and so on, as long as the ``rect``
is “alive”.

But no longer. That's what the ``if`` is for.
If we wanted to use this in a larger animation, where the blinking
rectangle only appears for a short time, we'd only want to schedule when
the rectangle is still on the scene.
It's good practice to do this even when our animation only includes this one
part.
Normally, objects are removed from the scene via the
:meth:`~gillcup_graphics.GraphicsObject.die` method, which sets the ``dead``
attribute.
So, we can use ``dead`` to see if it's necessary to schedule the next action.

All that's left is calling ``blink`` for the first time, and running the code:

.. literalinclude:: ../examples/02-clock.py
    :lines: 22-24

The ``run`` function starts the Pyglet main loop, which, in addition to taking
care of drawing our scene, feeds the current time to our ``clock``.
