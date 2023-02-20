from __future__ import annotations

from asyncio import Protocol
from collections.abc import Iterator
from copy import copy
from dataclasses import dataclass

from . import geometry


@dataclass(init=False)
class Vertex:
    vector: geometry.Vector2d

    def __init__(self, x: float, y: float) -> None:
        self.vector = geometry.Vector2d(x, y)

    @property
    def x(self) -> float:
        return self.vector.x

    @x.setter
    def x(self, value: float) -> None:
        self.vector.x = value

    @property
    def y(self) -> float:
        return self.vector.y

    @y.setter
    def y(self, value: float) -> None:
        self.vector.y = value


@dataclass
class Style:
    fill_color: str | None = "white"
    stroke_color: str | None = "black"
    stroke_width: int | None = 1


@dataclass(init=False)
class Shape(Protocol, geometry.Transformable):
    style: Style
    _vertices: list[Vertex]

    def __init__(
            self,
            *,
            style: Style | None = None,
    ) -> None:
        self._vertices = []
        self.style = style or Style()

    @property
    def vertices(self) -> list[Vertex]:
        return self._vertices[:]

    def __as_vectors__(self) -> Iterator[geometry.Vector2d]:
        return (vertex.vector for vertex in self._vertices)

    def __from_vectors__(self, vectors: Iterator[geometry.Vector2d]) -> Shape:
        new_shape = copy(self)

        new_vertices = []
        for _ in range(len(self._vertices)):
            vector = next(vectors)
            new_vertex = Vertex(vector.x, vector.y)
            new_vertices.append(new_vertex)

        new_shape._vertices = new_vertices

        return new_shape

    def __copy__(self) -> Shape: ...


@dataclass(init=False)
class Line(Shape):

    def __init__(
            self,
            start: Vertex,
            end: Vertex,
            /,
            *,
            style: Style | None = None,
    ) -> None:
        super().__init__(style=style)
        self._vertices = [start, end]

    @property
    def start(self) -> Vertex:
        return self._vertices[0]

    @property
    def end(self) -> Vertex:
        return self._vertices[1]

    def __copy__(self) -> Line:
        new_instance = Line(Vertex(0, 0), Vertex(0, 0))
        new_instance._vertices = [
            Vertex(v.x, v.y)
            for v in self._vertices
        ]

        return new_instance


@dataclass(init=False)
class Polygon(Shape):

    def __init__(self, *vertices: Vertex, style: Style | None = None) -> None:
        super().__init__(style=style)
        self._vertices = list(vertices)

    def add_vertex(self, vertex: Vertex) -> Polygon:
        self._vertices.append(vertex)

        return self


@dataclass(init=False)
class Rect(Polygon):

    def __init__(
            self,
            origin: Vertex,
            extent: Vertex,
            /,
            *,
            style: Style | None = None,
    ) -> None:
        x, y = origin.x, origin.y
        width, height = extent.x, extent.y

        super().__init__(
            Vertex(x, y),
            Vertex(x + width, y),
            Vertex(x + width, y + height),
            Vertex(x, y + height),
            style=style
        )

    @property
    def origin(self) -> Vertex:
        return self._vertices[0]

    @property
    def extent(self) -> Vertex:
        return Vertex(
            self.top_right.x - self.bottom_left.x,
            self.top_right.y - self.bottom_left.y,
        )

    bottom_left = origin

    @property
    def bottom_right(self) -> Vertex:
        return self._vertices[1]

    @property
    def top_left(self) -> Vertex:
        return self._vertices[3]

    @property
    def top_right(self) -> Vertex:
        return self._vertices[2]

    def __copy__(self) -> Rect:
        new_instance = Rect(Vertex(0, 0), Vertex(0, 0))
        new_instance._vertices = [
            Vertex(v.x, v.y)
            for v in self._vertices
        ]

        return new_instance
