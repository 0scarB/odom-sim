import math

from .geometry import (
    AffineTransformation,
    approx_equals,
    det,
    Matrix2x2,
    Matrix3x3,
    Vector2d,
    rotate,
    scale,
    transform,
    translate,
    undo_transform,
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


def test_affine_transformation_translate() -> None:
    assert transform(
        Vector2d(3, 4),
        AffineTransformation().translate(Vector2d(1, 2))
    ) == transform(
        3, 4, 
        AffineTransformation().translate(1, 2)
    ) == transform(
        Vector2d(3, 4),
        AffineTransformation().translate(
            Vector2d(1, 2),
            "right-then-forward",
        )
    ) == transform(
        Vector2d(3, 4),
        AffineTransformation().translate(
            Vector2d(1, 2),
            ">^",
        )
    ) == transform(
        Vector2d(3, 4),
        AffineTransformation().translate(
            -1, 2,
            "<^",
        )
    ) == transform(
        Vector2d(3, 4),
        AffineTransformation().translate(
            -1, -2,
            "<v",
        ),
    ) == Vector2d(4, 6)


def test_affine_transformation_rotate() -> None:
    assert approx_equals([
        transform(math.sqrt(2), 0, AffineTransformation().rotate(3 * math.pi / 4)),
        transform(math.sqrt(2), 0, AffineTransformation().rotate(3 * math.pi / 4, "counterclockwise")),
        transform(math.sqrt(2), 0, AffineTransformation().rotate(3 * math.pi / 4, "<-.")),
        transform(math.sqrt(2), 0, AffineTransformation().rotate(5 * math.pi / 4, "clockwise")),
        transform(math.sqrt(2), 0, AffineTransformation().rotate(5 * math.pi / 4, ".->")),
        Vector2d(-1, 1),
    ], 1e-10)


def test_affine_transformation_scale() -> None:
    assert transform(
        Vector2d(3, 4), AffineTransformation().scale(2)
    ) == transform(
        Vector2d(3, 4), AffineTransformation().scale(2, "<>")
    ) == Vector2d(6, 8)

    assert transform(
        Vector2d(4, 5),
        AffineTransformation().scale(Vector2d(2, 3))
    ) == transform(
        4, 5,
        AffineTransformation().scale(2, 3)
    ) == transform(
        Vector2d(4, 5),
        AffineTransformation().scale(
            Vector2d(2, 3),
            "<>",
        )
    ) == transform(
        Vector2d(4, 5),
        AffineTransformation().scale(
            Vector2d(2, 3),
            "enlarge",
        )
    ) == transform(
        Vector2d(4, 5),
        AffineTransformation().scale(
            1 / 2, 1 / 3,
            "><",
        )
    ) == transform(
        Vector2d(4, 5),
        AffineTransformation().scale(
            1 / 2, 1 / 3,
            "shrink",
        )
    ) == Vector2d(8, 15)


def test_affine_transformation_chain() -> None:
    assert approx_equals(
        transform(
            -3, -4,
            AffineTransformation()
            .translate(2, 3)
            .transform(
                AffineTransformation()
                .rotate(3 * math.pi / 4)
                .scale(1 / math.sqrt(2))
            )
            .scale(100)
        ),
        Vector2d(100, 0),
        10e-10
    )


def test_affine_transformation_undo() -> None:
    t = AffineTransformation()\
        .translate(2, 3)\
        .rotate(3 * math.pi / 4)\
        .scale(1 / math.sqrt(2))
    v = Vector2d(-3, -4)

    vt = transform(v, t)

    assert approx_equals(v, undo_transform(vt, t), 1e-10)


def test_transform_translate() -> None:
    assert transform(
        Vector2d(3, 4),
        translate(Vector2d(1, 2))
    ) == transform(
        3, 4,
        translate(1, 2)
    ) == transform(
        Vector2d(3, 4),
        translate(Vector2d(1, 2), "right-then-forward")
    ) == transform(
        Vector2d(3, 4),
        translate(Vector2d(1, 2), ">^")
    ) == transform(
        Vector2d(3, 4),
        translate(-1, 2, "<^")
    ) == transform(
        Vector2d(3, 4),
        translate(-1, -2, "<v"),
    ) == Vector2d(4, 6)


def test_transform_rotate() -> None:
    assert approx_equals([
        transform(math.sqrt(2), 0, rotate(3 * math.pi / 4)),
        transform(math.sqrt(2), 0, rotate(3 * math.pi / 4, "counterclockwise")),
        transform(math.sqrt(2), 0, rotate(3 * math.pi / 4, "<-.")),
        transform(math.sqrt(2), 0, rotate(5 * math.pi / 4, "clockwise")),
        transform(math.sqrt(2), 0, rotate(5 * math.pi / 4, ".->")),
        Vector2d(-1, 1),
    ], 1e-10)


def test_transform_scale() -> None:
    assert transform(
        Vector2d(3, 4), scale(2)
    ) == transform(
        Vector2d(3, 4), AffineTransformation().scale(2, "<>")
    ) == Vector2d(6, 8)

    assert transform(
        Vector2d(4, 5),
        scale(Vector2d(2, 3))
    ) == transform(
        4, 5,
        scale(2, 3)
    ) == transform(
        Vector2d(4, 5),
        scale(Vector2d(2, 3), "<>")
    ) == transform(
        Vector2d(4, 5),
        scale(Vector2d(2, 3), "enlarge")
    ) == transform(
        Vector2d(4, 5),
        scale(1/2, 1/3, "><")
    ) == transform(
        Vector2d(4, 5),
        scale(1/2, 1/3, "shrink")
    ) == Vector2d(8, 15)
