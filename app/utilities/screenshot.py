from kivy.graphics.fbo import Fbo
from kivy.graphics import Translate, ClearColor, ClearBuffers


def screenshot(widget, filename='output.png', region=None):
    if widget.parent is not None:
        canvas_parent_index = widget.parent.canvas.indexof(widget.canvas)
        widget.parent.canvas.remove(widget.canvas)

    fbo = Fbo(size=widget.size)

    with fbo:
        ClearColor(0, 0, 0, 0)
        ClearBuffers()
        Translate(-widget.x, -widget.y, 0)

    fbo.add(widget.canvas)
    fbo.draw()
    fbo.texture.save(filename)
    fbo.remove(widget.canvas)

    if widget.parent is not None:
        widget.parent.canvas.insert(canvas_parent_index, widget.canvas)

    return True


def screenshot_texture(widget, factory_func):
    if widget.parent is not None:
        canvas_parent_index = widget.parent.canvas.indexof(widget.canvas)
        widget.parent.canvas.remove(widget.canvas)

    fbo = Fbo(size=widget.size)

    with fbo:
        ClearColor(0, 0, 0, 0)
        ClearBuffers()
        Translate(-widget.x, -widget.y, 0)

    fbo.add(widget.canvas)
    fbo.draw()

    result = factory_func(fbo.texture)

    fbo.remove(widget.canvas)

    if widget.parent is not None:
        widget.parent.canvas.insert(canvas_parent_index, widget.canvas)

    return result