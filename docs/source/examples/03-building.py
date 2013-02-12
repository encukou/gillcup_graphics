from gillcup_graphics import Layer, Rectangle, Window, run, RealtimeClock
from gillcup import Animation

root_layer = Layer()

rect = Rectangle(root_layer,
        size=(0.5, 0.5),
        position=(0.25, 0.25),
        relative_anchor=(0.5, 0.5),
    )

Window(root_layer, width=400, height=400)

clock = RealtimeClock()


def announce_end():
    print('done')

animation = (
    Animation(rect, 'x', 0.75, time=1) +
    0.5 +  # a half-second delay
    Animation(rect, 'y', 0.75, time=1))
animation += [0.5, Animation(rect, 'x', 0.25, time=1), 0.5]
animation += (
    Animation(rect, 'y', 0.25, time=1) |
    Animation(rect, 'rotation', -90, time=1))
animation += announce_end

clock.schedule(animation)

run()
