"""Shiny graphical flashiness for Gillcup

Gillcup Graphics provides a number of modules:

.. toctree::
    :maxdepth: 1

    objects
    mainwindow
    transformation
    effectlayer

The most interesting classes of each module are exported directly
from the gillcup_graphics package:

* :class:`~gillcup_graphics.GraphicsObject` \
    (from :mod:`gillcup_graphics.objects`)
* :class:`~gillcup_graphics.Layer` \
    (from :mod:`gillcup_graphics.objects`)
* :class:`~gillcup_graphics.DecorationLayer` \
    (from :mod:`gillcup_graphics.objects`)
* :class:`~gillcup_graphics.Rectangle` \
    (from :mod:`gillcup_graphics.objects`)
* :class:`~gillcup_graphics.Sprite` \
    (from :mod:`gillcup_graphics.objects`)
* :class:`~gillcup_graphics.Text` \
    (from :mod:`gillcup_graphics.objects`)
* :class:`~gillcup_graphics.Window` \
    (from :mod:`gillcup_graphics.mainwindow`)
* :class:`~gillcup_graphics.RealtimeClock` \
    (from :mod:`gillcup_graphics.mainwindow`)
* :func:`~gillcup_graphics.run` \
    (from :mod:`gillcup_graphics.mainwindow`)
"""

__version__ = '0.2.0-alpha.1'
__version_info__ = (0, 2, 0, 'alpha', 1)

from gillcup_graphics.objects import (
    GraphicsObject, Layer, DecorationLayer, Rectangle, Sprite, Text)
from gillcup_graphics.effectlayer import EffectLayer
from gillcup_graphics.mainwindow import Window, RealtimeClock, run
