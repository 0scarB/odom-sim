from __future__ import annotations

import abc
import math
from abc import ABC
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, overload, Iterator, Literal, NoReturn, Protocol
from typing_extensions import Self


_TranslationDirection = Literal[
    "left-then-forward" , "<^",
    "left-then-down"    , "<v",
    "right-then-forward", ">^",
    "right-then-down"   , ">v",
]


_RotationDirection = Literal[
    "clockwise"       , "<-.",
    "counterclockwise", ".->",
]

_ScaleDirection = Literal[
    "enlarge", "<>",
    "shrink" , "><"
]


def vector(x: float, y: float) -> Vector2d:
    return Vector2d(x, y)


@overload
def transform(vector: Vector2d, transformation: Transformation2d) -> Vector2d: ...


@overload
def transform(x: float, y: float, transformation: Transformation2d) -> Vector2d: ...


def transform(*args: float | Vector2d | Transformation2d) -> Vector2d:
    *args, transformation = args
    return transformation.__apply_transform_to__(*args)


@overload
def undo_transform(vector: Vector2d, transformation: Transformation2d) -> Vector2d: ...


@overload
def undo_transform(x: float, y: float, transformation: Transformation2d) -> Vector2d: ...


def undo_transform(*args: float | Vector2d | Transformation2d) -> Vector2d:
    *args, transformation = args
    return transformation.__remove_transform_from__(*args)


@overload
def translate(vector: Vector2d) -> AffineTransformation: ...


@overload
def translate(vector: Vector2d, direction: _TranslationDirection) -> AffineTransformation: ...


@overload
def translate(x: float, y: float) -> AffineTransformation: ...


@overload
def translate(x: float, y: float, direction: _TranslationDirection) -> AffineTransformation: ...


def translate(*args: float | Vector2d | _TranslationDirection) -> AffineTransformation:
    return AffineTransformation().translate(*args)


@overload
def rotate(angle: float) -> AffineTransformation: ...


@overload
def rotate(angle: float, direction: _RotationDirection) -> AffineTransformation: ...


def rotate(*args: float | _RotationDirection) -> AffineTransformation:
    return AffineTransformation().rotate(*args)


@overload
def scale(vector: Vector2d) -> AffineTransformation: ...


@overload
def scale(vector: Vector2d, direction: _ScaleDirection) -> AffineTransformation: ...


@overload
def scale(x: float, y: float) -> AffineTransformation: ...


@overload
def scale(x: float, y: float, direction: _ScaleDirection) -> AffineTransformation: ...


@overload
def scale(x_and_y: float) -> AffineTransformation: ...


@overload
def scale(x_and_y: float, direction: _ScaleDirection) -> AffineTransformation: ...


def scale(*args: float | Vector2d | _ScaleDirection) -> AffineTransformation:
    return AffineTransformation().scale(*args)


class Transformation2d(Protocol):

    @overload
    def __apply_transform_to__(self, vector: Vector2d) -> Vector2d: ...

    @overload
    def __apply_transform_to__(self, x: float, y: float) -> Vector2d: ...

    def __apply_transform_to__(self, *args: float | Vector2d) -> Vector2d: ...

    @overload
    def __remove_transform_from__(self, vector: Vector2d) -> Vector2d: ...

    @overload
    def __remove_transform_from__(self, x: float, y: float) -> Vector2d: ...

    def __remove_transform_from__(self, *args: float | Vector2d) -> Vector2d: ...


@dataclass(init=False)
class AffineTransformation(Transformation2d):
    matrix: Matrix3x3

    @classmethod
    def _from_matrix(cls, matrix: Matrix3x3) -> Self:
        inst = cls()

        inst.matrix = matrix

        return inst

    def __init__(self):
        self.matrix = Matrix3x3(
            (1, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
        )

    def transform(self, transformation: Self) -> Self:
        return self._from_matrix(transformation.matrix * self.matrix)

    @overload
    def translate(self, vector: Vector2d) -> Self: ...

    @overload
    def translate(self, vector: Vector2d, direction: _TranslationDirection) -> Self: ...

    @overload
    def translate(self, x: float, y: float) -> Self: ...

    @overload
    def translate(self, x: float, y: float, direction: _TranslationDirection) -> Self: ...

    def translate(self, *args: float | Vector2d | _TranslationDirection) -> Self:
        if type(args[-1]) is str:
            *args, direction = args
        else:
            direction = "right-then-up"

        if len(args) == 1:
            translation_vector = args[0]
            x, y = translation_vector.x, translation_vector.y
        else:
            x, y = args

        if direction == "left-then-up" or direction == "<^":
            return self.translate(-x, y)

        if direction == "left-then-down" or direction == "<v":
            return self.translate(-x, -y)

        if direction == "right-then-down" or direction == ">v":
            return self.translate(x, -y)

        return self._from_matrix(Matrix3x3(
            (1, 0, x),
            (0, 1, y),
            (0, 0, 1)
        ) * self.matrix)

    @overload
    def rotate(self, angle: float) -> Self: ...

    @overload
    def rotate(self, angle: float, direction: _RotationDirection) -> Self: ...

    def rotate(self, *args) -> Self:
        if type(args[-1]) is str:
            *args, direction = args
        else:
            direction = "counterclockwise"

        angle = args[0]

        if direction == "clockwise" or direction == ".->":
            return self.rotate(-angle)

        return self._from_matrix(Matrix3x3(
            (math.cos(angle), -math.sin(angle), 0),
            (math.sin(angle),  math.cos(angle), 0),
            (0              ,  0              , 1),
        ) * self.matrix)

    @overload
    def scale(self, vector: Vector2d) -> Self: ...

    @overload
    def scale(self, vector: Vector2d, direction: _ScaleDirection) -> Self: ...

    @overload
    def scale(self, x: float, y: float) -> Self: ...

    @overload
    def scale(self, x: float, y: float, direction: _ScaleDirection) -> Self: ...

    @overload
    def scale(self, x_and_y: float) -> Self: ...

    @overload
    def scale(self, x_and_y: float, direction: _ScaleDirection) -> Self: ...

    def scale(self, *args: float | Vector2d | _ScaleDirection) -> Self:
        if type(args[-1]) is str:
            *args, direction = args
        else:
            direction: _ScaleDirection = "enlarge"

        if len(args) == 1:
            arg = args[0]

            if isinstance(arg, Vector2d):
                x, y = arg.x, arg.y
            else:
                x = y = arg
        else:
            x, y = args

        if direction == "shrink" or direction == "><":
            x, y = 1 / x, 1 / y

        return self._from_matrix(Matrix3x3(
            (x, 0, 0),
            (0, y, 0),
            (0, 0, 1),
        ) * self.matrix)

    def invert(self) -> Self:
        return self._from_matrix(self.matrix ** -1)

    def __apply_transform_to__(self, *args: float | Vector2d) -> Vector2d:
        if len(args) == 1:
            vector = args[0]

            x, y = vector.x, vector.y
        else:
            x, y = args

        vec3 = Vector3d(x, y, 1)

        transformed_vec3 = self.matrix * vec3

        return Vector2d(
            transformed_vec3.x,
            transformed_vec3.y,
        )

    def __remove_transform_from__(self, *args: float | Vector2d) -> Vector2d:
        if len(args) == 1:
            vector = args[0]

            x, y = vector.x, vector.y
        else:
            x, y = args

        vec3 = Vector3d(x, y, 1)

        transformed_vec3 = self.matrix**-1 * vec3

        return Vector2d(
            transformed_vec3.x,
            transformed_vec3.y,
        )


class SupportsApproxEquals(Protocol):

    def __approx_equals__(self, other: Self, threshold: float) -> bool: ...


@dataclass(init=False)
class Vector2d(SupportsApproxEquals):
    x: float
    y: float

    def __init__(self, x: float | int, y: float | int) -> None:
        self.x = float(x)
        self.y = float(y)

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        elif index == 1:
            return self.y

        raise IndexError(f"{type(self).__name__} only has 2 axes")

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __add__(self, other: Any) -> Self:
        if isinstance(other, type(self)):
            return type(self)(self.x + other.x, self.y + other.y)

        raise TypeError(
            f"{type(self).__name__} can only be added to another {type(self).__name__}"
        )

    def __mul__(self, other: Any) -> Self:
        if type(other) in frozenset({int, float}):
            return type(self)(other * self.x, other * self.y)

        raise TypeError(
            f"{type(self).__name__} can only be multiplied by a scalar integer of float"
        )

    def __repr__(self) -> str:
        return f"vec2({self.x}, {self.y})"

    def __str__(self) -> str:
        col_width = max(len(f"{val:.5}") for val in self)

        return (
            f"/{self.x:<{col_width}.5}\\\n"
            f"\\{self.y:<{col_width}.5}/"
        )

    def __approx_equals__(self, other: Self, threshold: float) -> bool:
        return (
                approx_equals(self.x, other.x, threshold)
                and approx_equals(self.y, other.y, threshold)
        )


@dataclass(init=False)
class Vector3d(SupportsApproxEquals):
    x: float
    y: float
    z: float

    def __init__(self, x: float | int, y: float | int, z: float | int) -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __getitem__(self, index: int) -> float:
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        elif index == 2:
            return self.z

        raise IndexError(f"{type(self).__name__} only has 3 axes")

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y
        yield self.z

    def __add__(self, other: Any) -> Self:
        if isinstance(other, type(self)):
            return type(self)(self.x + other.x, self.y + other.y, self.z + other.z)

        raise TypeError(
            f"{type(self).__name__} can only be added to another {type(self).__name__}"
        )

    def __mul__(self, other: Any) -> Self:
        if type(other) in frozenset({int, float}):
            return type(self)(other * self.x, other * self.y, other * self.z)

        if isinstance(other, Matrix3x3):
            # Implemented by 3x3 matrix
            return NotImplemented

        raise TypeError(
            f"{type(self).__name__} can only be multiplied by a scalar integer of float"
        )

    def __repr__(self) -> str:
        return f"vec3({self.x}, {self.y}, {self.z})"

    def __str__(self) -> str:
        col_width = max(len(f"{val:.5}") for val in self)

        return (
            f"/{self.x:<{col_width}.5}\\\n"
            f"|{self.y:<{col_width}.5}|\n"
            f"\\{self.z:<{col_width}.5}/"
        )

    def __approx_equals__(self, other: Self, threshold: float) -> bool:
        return (
                approx_equals(self.x, other.x, threshold)
                and approx_equals(self.y, other.y, threshold)
                and approx_equals(self.z, other.z, threshold)
        )


class SupportsDeterminant(Protocol):

    def __det__(self) -> float: ...


def det(val: SupportsDeterminant) -> float:
    return val.__det__()


class _BaseMatrix(SupportsApproxEquals, SupportsDeterminant, ABC):

    @overload
    def __pow__(self, exponent: Any) -> NoReturn: ...

    @overload
    def __pow__(self, exponent: Literal[1, -1, "T"]) -> Self: ...

    def __pow__(self, exponent: Any) -> Self | None:
        if exponent == 1:
            return self.__copy__()

        if exponent == -1:
            return self.__inverse__()

        if exponent == "T":
            return self.__transpose__()

        raise TypeError(
            f"{type(self).__name__} only accepts 1, -1, and 'T' as exponents"
        )

    @abc.abstractmethod
    def __transpose__(self) -> Self: ...

    @abc.abstractmethod
    def __inverse__(self) -> Self: ...

    @abc.abstractmethod
    def __copy__(self) -> Self: ...


@dataclass(init=False)
class Matrix2x2(_BaseMatrix):
    _matrix: tuple[
        tuple[float, float],
        tuple[float, float],
    ]

    def __init__(
            self,
            row1: tuple[float | int, float | int],
            row2: tuple[float | int, float | int],
            /,
    ) -> None:
        self._matrix = (
            tuple(float(val) for val in row1),
            tuple(float(val) for val in row2),
        )

    def __getitem__(self, index: int) -> tuple[float, float]:
        return self._matrix[index]

    def __iter__(self) -> Iterator[
        tuple[float, float],
    ]:
        return iter(self._matrix)

    @overload
    def __mul__(self, other: Any) -> NoReturn: ...

    @overload
    def __mul__(self, matrix2x2: Self) -> Self: ...

    @overload
    def __mul__(self, vector2d: Vector2d) -> Vector2d: ...

    def __mul__(self, other: Any) -> Self | Vector2d | NoReturn:
        if isinstance(other, Vector2d):
            return self._multiply_by_vector(other)

        if isinstance(other, type(self)):
            return self._multiply_by_matrix(other)

        raise TypeError(
            f"{type(self).__name__} can only have a 2x2 matrix or vector with 2 rows after multiplication operand"
        )

    @overload
    def __rmul__(self, other: Any) -> NoReturn: ...

    @overload
    def __rmul__(self, other: float | int) -> Self: ...

    def __rmul__(self, other: Any) -> Self | NoReturn:
        if (type_ := type(other)) is float or type_ is int:
            return self._multiply_by_scalar(other)

        raise TypeError(
            f"{type(self).__name__} can only have a 2x2 matrix or scalar before the multiplication operand"
        )

    def __repr__(self) -> str:
        return f"mat2x2({self[0]}, {self[1]})"

    def __str__(self) -> str:
        col_widths = [
            max(len(f"{self[row][column]:.5}") for row in range(2))
            for column in range(2)
        ]

        formatted_vals = [
            [f"{self[row][column]:<{col_widths[column]}.5}" for column in range(2)]
            for row in range(2)
        ]

        return (
            f"/{formatted_vals[0][0]},  {formatted_vals[0][1]}\\\n"
            f"|{formatted_vals[1][0]},  {formatted_vals[1][1]}|\n"
        )

    def __det__(self) -> float:
        return self[0][0] * self[1][1] - self[0][1] * self[1][0]

    def __transpose__(self) -> Self:
        return type(self)(
            (self[0][0], self[1][0]),
            (self[0][1], self[1][1]),
        )

    def __inverse__(self) -> Self:
        return (1 / det(self)) * type(self)(
            (self[0][0], -self[0][1]),
            (-self[1][0], self[1][1])
        )

    def __approx_equals__(self, other: Self, threshold: float) -> bool:
        return all(
            approx_equals(self[row][column], other[row][column], threshold)
            for row in range(2)
            for column in range(2)
        )

    def __copy__(self) -> Self:
        return type(self)(self._matrix[0], self._matrix[1])

    def _multiply_by_vector(self, vector: Vector2d) -> Vector2d:
        return Vector2d(
            self[0][0] * vector[0] + self[0][1] * vector[1],
            self[1][0] * vector[1] + self[1][1] * vector[1],
        )

    def _multiply_by_matrix(self, matrix: Self) -> Self:
        return type(self)(
            (
                self[0][0] * matrix[0][0] + self[0][1] * matrix[1][0],
                self[0][0] * matrix[0][1] + self[0][1] * matrix[1][1],
            ),
            (
                self[1][0] * matrix[0][0] + self[1][1] * matrix[1][0],
                self[1][0] * matrix[0][1] + self[1][1] * matrix[1][1],
            ),
        )

    def _multiply_by_scalar(self, scalar: float | int) -> Self:
        return type(self)(
            (scalar * self[0][0], scalar * self[0][1]),
            (scalar * self[1][0], scalar * self[1][1])
        )


@dataclass(init=False)
class Matrix3x3(_BaseMatrix):
    _matrix: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]

    def __init__(
            self,
            row1: tuple[float | int, float | int, float | int],
            row2: tuple[float | int, float | int, float | int],
            row3: tuple[float | int, float | int, float | int],
            /,
    ) -> None:
        self._matrix = (
            tuple(float(val) for val in row1),
            tuple(float(val) for val in row2),
            tuple(float(val) for val in row3)
        )

    def __getitem__(self, index: int) -> tuple[float, float, float]:
        return self._matrix[index]

    def __iter__(self) -> Iterator[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]:
        return iter(self._matrix)

    @overload
    def __mul__(self, other: Any) -> NoReturn: ...

    @overload
    def __mul__(self, matrix3x3: Self) -> Self: ...

    @overload
    def __mul__(self, vector3d: Vector3d) -> Vector3d: ...

    def __mul__(self, other: Any) -> Self | Vector3d | NoReturn:
        if isinstance(other, Vector3d):
            return self._multiply_by_vector(other)

        if isinstance(other, type(self)):
            return self._multiply_by_matrix(other)

        raise TypeError(
            f"{type(self).__name__} can only have a 3x3 matrix or vector with 3 rows after multiplication operand"
        )

    @overload
    def __rmul__(self, other: Any) -> NoReturn: ...

    @overload
    def __rmul__(self, other: float | int) -> Self: ...

    def __rmul__(self, other: Any) -> Self | NoReturn:
        if (type_ := type(other)) is float or type_ is int:
            return self._multiply_by_scalar(other)

        raise TypeError(
            f"{type(self).__name__} can only have a 3x3 matrix or scalar before the multiplication operand"
        )

    def __repr__(self) -> str:
        return f"mat3x3({self[0]}, {self[1]}, {self[2]})"

    def __str__(self) -> str:
        col_widths = [
            max(len(f"{self[row][column]:.5}") for row in range(3))
            for column in range(3)
        ]

        formatted_vals = [
            [f"{self[row][column]:<{col_widths[column]}.5}" for column in range(3)]
            for row in range(3)
        ]

        return (
            f"/{formatted_vals[0][0]},  {formatted_vals[0][1]},  {formatted_vals[0][2]}\\\n"
            f"|{formatted_vals[1][0]},  {formatted_vals[1][1]},  {formatted_vals[1][2]}|\n"
            f"\\{formatted_vals[2][0]},  {formatted_vals[2][1]},  {formatted_vals[2][2]}/"
        )

    def __det__(self) -> float:
        # Rule of Sarrus
        return (
                self[0][0] * self[1][1] * self[2][2]
                + self[0][1] * self[1][2] * self[2][0]
                + self[0][2] * self[1][0] * self[2][1]
                - self[0][2] * self[1][1] * self[2][0]
                - self[0][0] * self[1][2] * self[2][1]
                - self[0][1] * self[1][0] * self[2][2]
        )

    def __inverse__(self) -> Self:
        return (1 / det(self)) * type(self)(
            (
                self[1][1] * self[2][2] - self[1][2] * self[2][1],
                - (self[1][0] * self[2][2] - self[1][2] * self[2][0]),
                self[1][0] * self[2][1] - self[1][1] * self[2][0]
            ),
            (
                - (self[0][1] * self[2][2] - self[0][2] * self[2][1]),
                self[0][0] * self[2][2] - self[0][2] * self[2][0],
                - (self[0][0] * self[2][1] - self[0][1] * self[2][0])
            ),
            (
                self[0][1] * self[1][2] - self[0][2] * self[1][1],
                - (self[0][0] * self[1][2] - self[0][2] * self[1][0]),
                self[0][0] * self[1][1] - self[0][1] * self[1][0]
            )
        ) ** "T"

    def __transpose__(self) -> Self:
        return type(self)(
            (self[0][0], self[1][0], self[2][0]),
            (self[0][1], self[1][1], self[2][1]),
            (self[0][2], self[1][2], self[2][2]),
        )

    def __copy__(self) -> Self:
        return type(self)(self._matrix[0], self._matrix[1], self._matrix[2])

    def __approx_equals__(self, other: Self, threshold: float) -> bool:
        return all(
            approx_equals(self[row][column], other[row][column], threshold)
            for row in range(3)
            for column in range(3)
        )

    def _multiply_by_vector(self, vector: Vector3d) -> Vector3d:
        return Vector3d(
            self[0][0] * vector[0] + self[0][1] * vector[1] + self[0][2] * vector[2],
            self[1][0] * vector[0] + self[1][1] * vector[1] + self[1][2] * vector[2],
            self[2][0] * vector[0] + self[2][1] * vector[1] + self[2][2] * vector[2],
        )

    def _multiply_by_matrix(self, matrix: Self) -> Self:
        return type(self)(
            (
                self[0][0] * matrix[0][0] + self[0][1] * matrix[1][0] + self[0][2] * matrix[2][0],
                self[0][0] * matrix[0][1] + self[0][1] * matrix[1][1] + self[0][2] * matrix[2][1],
                self[0][0] * matrix[0][2] + self[0][1] * matrix[1][2] + self[0][2] * matrix[2][2],
            ),
            (
                self[1][0] * matrix[0][0] + self[1][1] * matrix[1][0] + self[1][2] * matrix[2][0],
                self[1][0] * matrix[0][1] + self[1][1] * matrix[1][1] + self[1][2] * matrix[2][1],
                self[1][0] * matrix[0][2] + self[1][1] * matrix[1][2] + self[1][2] * matrix[2][2],
            ),
            (
                self[2][0] * matrix[0][0] + self[2][1] * matrix[1][0] + self[2][2] * matrix[2][0],
                self[2][0] * matrix[0][1] + self[2][1] * matrix[1][1] + self[2][2] * matrix[2][1],
                self[2][0] * matrix[0][2] + self[2][1] * matrix[1][2] + self[2][2] * matrix[2][2],
            ),
        )

    def _multiply_by_scalar(self, scalar: float | int) -> Self:
        return type(self)(
            (scalar * self[0][0], scalar * self[0][1], scalar * self[0][2]),
            (scalar * self[1][0], scalar * self[1][1], scalar * self[1][2]),
            (scalar * self[2][0], scalar * self[2][1], scalar * self[2][2])
        )


@overload
def approx_equals(a: SupportsApproxEquals | float, b: SupportsApproxEquals | float, /, threshold: float) -> bool: ...


@overload
def approx_equals(items: Iterable[SupportsApproxEquals | float], /, threshold: float) -> bool: ...


def approx_equals(
        *args: SupportsApproxEquals | float | Iterable[SupportsApproxEquals | float] | float,
        **kwargs: float,
) -> bool:
    try:
        threshold = kwargs["threshold"]
    except KeyError:
        *args, threshold = args

    if len(args) == 2:
        a, b = args
        return approx_equals((a, b), threshold)

    args = list(*args)
    for i, a in enumerate(args[:-1]):
        for b in args[i + 1:]:
            try:
                if not a.__approx_equals__(b, threshold):
                    return False
            except AttributeError:
                if not a - threshold <= b <= a + threshold:
                    return False

    return True
