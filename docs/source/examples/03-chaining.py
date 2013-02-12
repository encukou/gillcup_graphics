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
    print 'done'

animation = Animation(rect, 'x', 0.75, time=1)

clock.schedule(animation)

animation = animation.chain(Animation(rect, 'y', 0.75, time=1))
animation = animation.chain(Animation(rect, 'x', 0.25, time=1))
animation = animation.chain(Animation(rect, 'y', 0.25, time=1))

animation.chain(announce_end)

run()
