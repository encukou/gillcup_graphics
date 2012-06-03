from __future__ import division

import gillcup
import gillcup_graphics


class DemoRect(gillcup_graphics.Rectangle):
    """A rectangle that goes purple on hover and blue on click/hold/drag
    """
    def __init__(self, parent, clock, **kwargs):
        super(DemoRect, self).__init__(parent, **kwargs)
        self.clock = clock
        self.pointers_in = set()
        self.pointers_pressed = set()

    def on_pointer_motion(self, pointer, x, y, z, **kwargs):
        if pointer not in self.pointers_in:
            self.clock.schedule(gillcup.Animation(self, 'red', 0, time=0.15))
        self.pointers_in.add(pointer)
        return True

    def on_pointer_leave(self, pointer, x, y, z, **kwargs):
        self.pointers_in.remove(pointer)
        if not self.pointers_in:
            self.clock.schedule(gillcup.Animation(self, 'red', 1, time=0.15))
        return True

    def on_pointer_press(self, pointer, x, y, z, button, **kwargs):
        if not self.pointers_pressed:
            self.clock.schedule(gillcup.Animation(self, 'green', 0, time=0.15))
        self.pointers_pressed.add((pointer, button))
        return True

    def on_pointer_release(self, pointer, x, y, z, button, **kwargs):
        self.pointers_pressed.remove((pointer, button))
        if not self.pointers_pressed:
            self.clock.schedule(gillcup.Animation(self, 'green', 1, time=0.15))
        return True


class DraggableRect(gillcup_graphics.Rectangle):
    """A rectangle that can be dragged around, but is "transparent" to hover

    N.B.: This simple mechanism will not work with objects that are scaled or
    rotated.
    """
    def __init__(self, parent, **kwargs):
        super(DraggableRect, self).__init__(parent, **kwargs)
        self.drag_starts = {}

    def on_pointer_press(self, pointer, x, y, z, button, **kwargs):
        self.drag_starts[pointer, button] = x, y
        return True

    def on_pointer_drag(self, pointer, x, y, z, button, **kwargs):
        start_x, start_y = self.drag_starts[pointer, button]
        self.x += x - start_x
        self.y += y - start_y
        return True

    def on_pointer_release(self, pointer, x, y, z, button, **kwargs):
        del self.drag_starts[pointer, button]
        return True


class DemoLayer(gillcup_graphics.Layer):
    def __init__(self, clock, *args, **kwargs):
        super(DemoLayer, self).__init__(*args, **kwargs)
        n = 10
        for x in range(n):
            for y in range(n):
                rct = DemoRect(self, clock, scale=(1 / n, 1 / n),
                    position=(x / n, y / n))
                if (x, y) == (5, 5):
                    rct.rotation = 30
                    rct.blue = 0.7
        DraggableRect(self, size=(0.05, 0.05), color=(0, 1, 0),
            position=(1 / 3, 1 / 3))


if __name__ == '__main__':
    clock = gillcup_graphics.RealtimeClock()
    layer = DemoLayer(clock)
    window = gillcup_graphics.Window(layer, width=500, height=500)
    gillcup_graphics.run()
