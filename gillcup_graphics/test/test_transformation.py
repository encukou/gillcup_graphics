"""Tests for the transformation module
"""

from __future__ import division

import math

from gillcup_graphics.transformation import (MatrixTransformation,
    PointTransformation)


def almost_equal(a, b):
    """Return true if the numbers a and b are very near each other"""
    return abs(a - b) < 0.00001


def sequences_almost_equal(a_seq, b_seq):
    """Return true if corresponding contents of lists a, b are alost_equal"""
    print a_seq, b_seq
    if len(a_seq) != len(b_seq):
        return False
    return all(almost_equal(a, b) for a, b in zip(a_seq, b_seq))


def matrix_almost_equal(matrix, *args):
    """Return true if elements of matrix are almost equal to args"""
    print '---'
    print tuple(matrix)
    print args
    for x in range(4):
        for y in range(4):
            if matrix[x, y] != matrix[x + y * 4]:
                return False
            if not almost_equal(matrix[x, y], args[x + y * 4]):
                return False
    return sequences_almost_equal(matrix, args)


def assert_identity(transformation):
    """Assert that the given transformation is an identity transformation"""
    transformation._assert_matrix_equal_(
        1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1,)


class TestPointTransformation(PointTransformation):
    def _assert_matrix_equal_(self, *values):
        matrix = MatrixTransformation()
        matrix.premultiply(values)
        print 'orig:', self.original_point
        assert sequences_almost_equal(
            self.point,
            matrix.transform_point(*self.original_point))


def pytest_generate_tests(metafunc):
    if "transformation" in metafunc.funcargnames:
        matrix_transformation = MatrixTransformation()
        def _assert_matrix_equal_(*values):
            assert matrix_almost_equal(matrix_transformation, *values)
        matrix_transformation._assert_matrix_equal_ = _assert_matrix_equal_

        points = [
                (0, 0, 0),
                (1, 0, 0),
                (0, 1, 0),
                (0, 0, 1),
                (1, 1, 1),
                (1, 2, 3),
                (-5, 80, 3.2),
                (4, 8.2, 0),
            ]

        metafunc.parametrize("transformation",
            [matrix_transformation] + [
                    TestPointTransformation(*p) for p in points],
            ids=['MatrixTransformation'] + points)


def pytest_funcarg__matrix(request):
    """Funcarg factory for a matrix"""
    return MatrixTransformation()


def distort(transformation):
    """Mangle the given transformation in some way"""
    transformation.translate(5, 6, 7)
    transformation.rotate(5, 1, 2, 3)
    transformation.scale(2, 3, 4)


def test_identity(transformation):
    """Ensure the transformation is identity by default"""
    assert_identity(transformation)


def test_translate(transformation):
    """Test general translation works"""
    transformation.translate(5, 6, 7)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            5, 6, 7, 1,
        )


def test_translate_x(transformation):
    """Test x-axis translation works"""
    transformation.translate(4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            4, 0, 0, 1,
        )
    transformation.translate(x=4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            8, 0, 0, 1,
        )


def test_translate_y(transformation):
    """Test y-axis translation works"""
    transformation.translate(0, 4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 4, 0, 1,
        )
    transformation.translate(y=4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 8, 0, 1,
        )


def test_translate_z(transformation):
    """Test z-axis translation works"""
    transformation.translate(0, 0, 4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 4, 1,
        )
    transformation.translate(z=4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 8, 1,
        )


def test_rotate_z(transformation):
    """Test z-axis rotation works"""
    transformation.rotate(180)
    transformation._assert_matrix_equal_(
            -1, 0, 0, 0,
            0, -1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )
    transformation.rotate(90)
    transformation._assert_matrix_equal_(
            0, -1, 0, 0,
            1, 0, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )
    transformation.rotate(45)
    transformation._assert_matrix_equal_(
            math.sqrt(2) / 2, -math.sqrt(2) / 2, 0, 0,
            math.sqrt(2) / 2, math.sqrt(2) / 2, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )


def test_rotate_y(transformation):
    """Test y-axis rotation works"""
    transformation.rotate(180, 0, 1, 0)
    transformation._assert_matrix_equal_(
            -1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, -1, 0,
            0, 0, 0, 1,
        )
    transformation.rotate(90, 0, 1, 0)
    transformation._assert_matrix_equal_(
            0, 0, 1, 0,
            0, 1, 0, 0,
            -1, 0, 0, 0,
            0, 0, 0, 1,
        )
    transformation.rotate(45, 0, 1, 0)
    transformation._assert_matrix_equal_(
            math.sqrt(2) / 2, 0, math.sqrt(2) / 2, 0,
            0, 1, 0, 0,
            -math.sqrt(2) / 2, 0, math.sqrt(2) / 2, 0,
            0, 0, 0, 1,
        )


def test_rotate_arbitrary(transformation):
    """Test general rotation works"""
    transformation.rotate(45, 1, 0.5, 1)
    transformation._assert_matrix_equal_(
            1, 0.8535534, -0.06066, 0,
            -0.56066, 0.78033, 0.8535534, 0,
            0.6464466, -0.56066, 1, 0,
            0, 0, 0, 1,
        )


def test_scale(transformation):
    """Test general scaling works"""
    transformation.scale(5, 6, 7)
    transformation._assert_matrix_equal_(
            5, 0, 0, 0,
            0, 6, 0, 0,
            0, 0, 7, 0,
            0, 0, 0, 1,
        )


def test_scale_x(transformation):
    """Test x-axis scaling works"""
    transformation.scale(4)
    transformation._assert_matrix_equal_(
            4, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )
    transformation.scale(x=4)
    transformation._assert_matrix_equal_(
            16, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )


def test_scale_y(transformation):
    """Test y-axis scaling works"""
    transformation.scale(1, 4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 4, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )
    transformation.scale(y=4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 16, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        )


def test_scale_z(transformation):
    """Test z-axis scaling works"""
    transformation.scale(1, 1, 4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 4, 0,
            0, 0, 0, 1,
        )
    transformation.scale(z=4)
    transformation._assert_matrix_equal_(
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 16, 0,
            0, 0, 0, 1,
        )


def test_push_pop(transformation):
    """Test that a pop restores state"""
    transformation.push()
    distort(transformation)
    transformation.pop()
    assert_identity(transformation)


def test_state(transformation):
    """Test the ``state`` context manager"""
    with transformation.state:
        distort(transformation)
    assert_identity(transformation)


def test_reset(transformation):
    """Test the transformation is identity after a reset"""
    distort(transformation)
    transformation.reset()
    assert_identity(transformation)


def test_premultiply_1(transformation):
    """Test premultiplication with some numbers off the top of my head"""
    values = [
            10, 11, 12, 0,
            14, 50, 16, 0,
            17, 18, 19, 0,
            12, 11, 10, 1,
        ]
    transformation.premultiply(values)
    transformation._assert_matrix_equal_(*values)


def test_premultiply_rotate_translate(transformation):
    """Test premultiplication with literal affine matrices"""
    transformation.premultiply((
            0, 0, 1, 0,
            0, 1, 0, 0,
            1, 0, 0, 0,
            0, 0, 0, 1,
        ))
    transformation.premultiply((
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            3, 4, 5, 1,
        ))
    transformation._assert_matrix_equal_(
            0, 0, 1, 0,
            0, 1, 0, 0,
            1, 0, 0, 0,
            5, 4, 3, 1,
        )


def test_premultiply_random(transformation):
    """Test premultiplication with (fixed) random numbers"""
    transformation.premultiply((
            309, 223, 296, 0,
            132, 737, 406, 0,
            534, 748, 442, 0,
            901, 862, 439, 1,
        ))
    transformation.premultiply((
            450, 526, 880, 0,
            655, 278, 232, 0,
            484, 286, 594, 0,
            327, 158, 564, 1,
        ))
    transformation._assert_matrix_equal_(
            678402, 1146252, 735716, 0,
            362979, 524487, 409292, 0,
            504504, 763026, 521928, 0,
            423976, 612101, 410667, 1
        )

def test_inverse(matrix):
    """Test taking the inverse of an affine matrix"""
    matrix.premultiply((
            30, 22, 96, 0,
            12, 77, 20, 0,
            34, 48, 42, 0,
            91, 62, 43, 1,
        ))
    assert sequences_almost_equal(matrix.inverse, (
            -0.018347588, -0.029724060, 0.056091657, 0,
            -0.001420042, 0.016169114, -0.004453768, 0,
            0.016475714, 0.005583347, -0.016507988, 0,
            1.049217363, 1.462320478, -4.118363724, 1,
        ))


def test_transform_point(matrix):
    """Test transforming a point"""
    matrix.scale(1 / 3, 1 / 3, 1 / 3)
    assert sequences_almost_equal(matrix.transform_point(1, 1, 1), (3, 3, 3))
    assert sequences_almost_equal(matrix.transform_point(0, 1, 1), (0, 3, 3))
    assert sequences_almost_equal(matrix.transform_point(1, 0, 1), (3, 0, 3))
    assert sequences_almost_equal(matrix.transform_point(1, 1, 0), (3, 3, 0))
    assert sequences_almost_equal(matrix.transform_point(2, 3, 4), (6, 9, 12))
    matrix.reset()
    matrix.rotate(90)
    assert sequences_almost_equal(matrix.transform_point(1, 1, 1), (1, -1, 1))
    assert sequences_almost_equal(matrix.transform_point(0, 1, 1), (1, 0, 1))
    assert sequences_almost_equal(matrix.transform_point(1, 0, 1), (0, -1, 1))
    assert sequences_almost_equal(matrix.transform_point(1, 1, 0), (1, -1, 0))
    assert sequences_almost_equal(matrix.transform_point(2, 3, 4), (3, -2, 4))
    matrix.reset()
    matrix.translate(-1, -2, -3)
    assert sequences_almost_equal(matrix.transform_point(1, 1, 1), (2, 3, 4))
    assert sequences_almost_equal(matrix.transform_point(0, 1, 1), (1, 3, 4))
    assert sequences_almost_equal(matrix.transform_point(1, 0, 1), (2, 2, 4))
    assert sequences_almost_equal(matrix.transform_point(1, 1, 0), (2, 3, 3))
    assert sequences_almost_equal(matrix.transform_point(2, 3, 4), (3, 5, 7))
