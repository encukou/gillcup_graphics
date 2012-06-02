from gillcup_graphics import Layer, Rectangle, Window, run, RealtimeClock

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
        rect.opacity = 1
    else:
        rect.opacity = 0

    if not rect.dead:
        clock.schedule(lambda: blink(not on), 0.5)

blink(True)

run()
