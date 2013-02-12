from gillcup_graphics import Layer, Text, Window, run

root_layer = Layer()

hi_world = Text(root_layer, 'Hello, World!',
        position=(0.5, 0.5),
        relative_anchor=(0.5, 0),
        scale=(0.001, 0.001),
    )

Window(root_layer, width=400, height=400)

run()
