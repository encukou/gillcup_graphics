gillcup_graphics.transformation
===============================

.. automodule:: gillcup_graphics.transformation

.. autoclass:: gillcup_graphics.transformation.BaseTransformation

    .. autoattribute:: gillcup_graphics.transformation.BaseTransformation.state
    .. automethod:: gillcup_graphics.transformation.BaseTransformation.push
    .. automethod:: gillcup_graphics.transformation.BaseTransformation.pop
    .. automethod:: gillcup_graphics.transformation.BaseTransformation.reset

    .. automethod:: gillcup_graphics.transformation.BaseTransformation.translate
    .. automethod:: gillcup_graphics.transformation.BaseTransformation.rotate
    .. automethod:: gillcup_graphics.transformation.BaseTransformation.scale
    .. automethod:: gillcup_graphics.transformation.BaseTransformation.premultiply

.. autoclass:: gillcup_graphics.transformation.GlTransformation

.. autoclass:: gillcup_graphics.transformation.TupleTransformation

    .. automethod:: gillcup_graphics.transformation.TupleTransformation.transform_point

.. class:: gillcup_graphics.transformation.MatrixTransformation

    Currently an alias of
    :class:`gillcup_graphics.transformation.TupleTransformation`

    May use a faster backend, such as Numpy if available, in the future
