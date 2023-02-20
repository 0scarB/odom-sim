from calculation.geometry import (
    approx_equals,
    det,
    Matrix2x2,
    Matrix3x3,
)


def test_matrix_determinants():
    m = Matrix3x3(
        (1, 2, 3),
        (3, 2, 1),
        (2, 1, 3)
    )

    assert det(m) == (
        m[0][0] * det(Matrix2x2(
            (m[1][1], m[1][2]),
            (m[2][1], m[2][2])
        ))
        - m[0][1] * det(Matrix2x2(
            (m[1][0], m[1][2]),
            (m[2][0], m[2][2])
        ))
        + m[0][2] * det(Matrix2x2(
            (m[1][0], m[1][1]),
            (m[2][0], m[2][1])
        ))
    ) == -12


def test_2x2_matrix_inverse():
    m = Matrix2x2(
        (1, 2),
        (3, 4)
    )
    inverse = m ** -1

    assert m == inverse ** -1


def test_3x3_matrix_inverse():
    m = Matrix3x3(
        (1, 2, 3),
        (3, 2, 1),
        (2, 1, 3)
    )
    inverse = m ** -1

    assert approx_equals(m, inverse ** -1, threshold=1e-10)
