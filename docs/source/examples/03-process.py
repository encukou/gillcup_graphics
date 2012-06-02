from gillcup_graphics import Layer, Rectangle, Window, run, RealtimeClock
from gillcup import Animation
from gillcup.actions import process_generator

root_layer = Layer()

rect = Rectangle(root_layer,
        size=(0.5, 0.5),
        position=(0.25, 0.25),
        relative_anchor=(0.5, 0.5),
    )

Window(root_layer, width=400, height=400)

clock = RealtimeClock()

@process_generator
def process():
    while not rect.dead:
        for prop, value in (
                ('x', 0.75),
                ('y', 0.75),
                ('x', 0.25),
                ('y', 0.25)):
            print('Animating {0} towards {1}'.format(prop, value))
            yield Animation(rect, prop, value, time=0.5, easing='sine.in_out')

clock.schedule(process())

run()
