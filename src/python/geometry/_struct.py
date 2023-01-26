from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any


@dataclass
class Vector:
    x: float
    y: float

    @property
    def magnitude(self) -> float:
        return sqrt(self.x ** 2 + self.y ** 2)

    def __add__(self, other: Any) -> Vector:
        if isinstance(other, Vector):
            return Vector(
                self.x + other.x,
                self.y + other.y,
            )

        raise TypeError

    def __mul__(self, other: Any) -> Vector:
        if type(other) in {float, int}:
            return Vector(
                other * self.x,
                other * self.y,
            )

        if isinstance(other, Vector):
            return Vector(
                self.x * other.x,
                self.y * other.y,
            )

        raise TypeError
