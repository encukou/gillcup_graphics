"""Test helper

When a test module does::

    from gillcup_graphics.test.recordinglayer import pytest_funcarg__layer

all test functions in it can use the ``layer`` funcarg, which records an image
of whatever is added to it, and compares it to a reference rendering in
gillcup_graphics/test/images/expected.
To account for different OpenGL implementations, 0.25% dissimilarity is
tolerated.

Images generated by the tests go in gillcup_graphics/test/images/expected.
If numpy is installed, you also get "report" images that should hopefully
make it clear what is different.

This all is achieved by an EffectLayer subclass, ad invisible Window, pytest
funcargs, numpy matrix stacking and other such arcane hackery.

"""

from __future__ import division

import os
import sys

import pyglet.image
try:
    if hasattr(sys, 'pypy_version_info'):
        # XXX: PyPy Numpy is not there yet
        numpy = None
    else:
        import numpy  # pylint: disable=F0401
except ImportError:  # pragma: no cover
    numpy = None

from gillcup_graphics.effectlayer import RecordingLayer

expected_dir = os.path.join(os.path.dirname(__file__), 'images', 'expected')
actual_dir = os.path.join(os.path.dirname(__file__), 'images', 'result')
legend_path = os.path.join(os.path.dirname(__file__), 'images', 'legend.png')

image_width = 100
image_height = 100


def try_unlink(path):
    """Unlink a file if it exists"""
    try:
        os.unlink(path)
    except OSError:
        pass


def get_data(image):
    """Retrieve pixel data from an image as 4 lists of bytestrings"""
    array = [list(ord(n) for n in image.get_data(c, image.width))
        for c in 'RGBA']
    return array


def write_diff_report(result, expected, filename):
    """Write an image illustrating differences between result & expected

    Requires numpy
    """
    result = numpy.array(result, int)
    expected = numpy.array(expected, int)
    result.shape = expected.shape = 4, image_height, image_width
    difference = abs(expected - result)
    alphadiff = expected.copy()
    alphadiff[3] = difference.sum(0) * 3 // 4 + 255 // 4
    zdiff = difference.copy()
    zdiff[3] = 255 - zdiff[3]
    diffdata = numpy.concatenate([result, expected, alphadiff, zdiff], 2)
    by_channel = None
    for current_channel in range(4):
        diff = difference.copy()
        diff[:3] = diff[current_channel]
        diff[3] = 255
        if by_channel is None:
            by_channel = diff
        else:
            by_channel = numpy.concatenate([by_channel, diff], 2)
    legend_image = pyglet.image.load(legend_path)
    legend = numpy.array(get_data(legend_image))
    legend.shape = 4, legend.size // (image_width * 4) // 4, image_width * 4
    diffdata = numpy.concatenate([
            by_channel,
            legend,
            diffdata
        ], 1)
    diffdata = diffdata.transpose([1, 2, 0]).clip(0, 255)
    diffdata = diffdata.reshape([diffdata.size])
    data_image = pyglet.image.ImageData(image_width * 4,
        image_height * 2 + legend_image.height,
        'RGBA', ''.join(chr(int(c)) for c in diffdata))
    data_image.save(filename)


class TestLayer(RecordingLayer):
    """RecordingLayer that can compare itself with reference rendering"""
    def __init__(self, name):
        super(TestLayer, self).__init__(name=name)

    def dissimilarity(self):
        """Do the image comparison"""
        name = self.name
        expected_filename = os.path.join(expected_dir, name + '.png')
        result_filename = os.path.join(actual_dir, name + '.png')
        diff_filename = os.path.join(actual_dir, name + '.report.png')

        try_unlink(result_filename)
        try_unlink(diff_filename)

        try:
            expected_image = pyglet.image.load(expected_filename)
            expected = get_data(expected_image)
        except IOError:
            expected = None
        if expected is None:
            raise AssertionError('Expected image not found.\n'
                'Expected:      %s\n'
                'Actual result: %s\n'
                '' % (expected_filename, result_filename))
        result_image = self.get_image(image_width, image_height)
        result = get_data(result_image)
        if expected == result:
            return 0
        result_image.save(result_filename)
        if numpy:
            write_diff_report(result, expected, diff_filename)
        # Compare premultiplied images
        def _get_diff(line1, line2):
            total = 0
            for pix1, pix2 in zip(zip(*[iter(line1)] * 4),
                    zip(*[iter(line2)] * 4)):
                a1 = pix1[3] / 255
                a2 = pix2[3] / 255
                alpha_diff = abs(a1 - a2) ** 2
                total += sum(abs(p1 / 255 * a1 - p2 / 255 * a2) ** 2
                    for p1, p2 in zip(pix1[:3], pix2[:3])) + alpha_diff
            return total
        differences = (_get_diff(e, r) for e, r in zip(result, expected))
        maximum_dis = 4 * image_width * image_height
        dissimilarity = sum(differences) / maximum_dis
        print ('Images not same.\n'
            'Dissimilarity: %.7s%%\n'
            'Expected:      %s\n'
            'Actual result: %s\n'
            'Report/deltas: %s\n'
            '' % (
                dissimilarity * 100,
                expected_filename, result_filename, diff_filename))
        return dissimilarity


def pytest_funcarg__layer(request):
    """A Layer funcarg that records its contents and checks them automatically

    A matching file name is auto-generated from the test name, and the result
    is compared to a reference rendering. If the reference rendering does not
    exist, or if the images differ, appropriate paths are output for human
    inspection and/or copying of files.
    """

    name = request.module.__name__
    if request.cls:
        name += '.' + request.cls.__name__
    name += '.' + request.function.__name__

    layer = TestLayer(name)

    return layer
