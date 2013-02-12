from gillcup_graphics import Layer, Rectangle, Window, run, RealtimeClock
from gillcup import Animation

root_layer = Layer()

rect = Rectangle(root_layer,
        size=(0.5, 0.5),
        position=(0.5, 0.5),
        relative_anchor=(0.5, 0.5),
        rotation=45,
    )

Window(root_layer, width=400, height=400)

clock = RealtimeClock()


def blink(on):
    if on:
        clock.schedule(Animation(rect, 'opacity', 1, time=0.3))
    else:
        clock.schedule(Animation(rect, 'opacity', 0, time=0.3))

    if not rect.dead:
        clock.schedule(lambda: blink(not on), 0.5)

blink(True)

clock.schedule(Animation(rect, 'rotation', 0, time=1, timing='infinite'))

clock.schedule(Animation(rect, 'color', 1, 0.5, 0, time=5))

run()
