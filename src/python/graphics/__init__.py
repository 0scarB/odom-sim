from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from copy import copy
from dataclasses import dataclass
from typing import ClassVar, Iterable

from ._color import Color
from ..geometry import Vector


class Point:
    _vector: Vector

    def __init__(self, x: float, y: float) -> None:
        self._vector = Vector(x, y)

    @property
    def x(self) -> float:
        return self._vector.x

    @x.setter
    def x(self, value: float) -> None:
        self._vector.x = value

    @property
    def y(self) -> float:
        return self._vector.y

    @y.setter
    def y(self, value: float) -> None:
        self._vector.y = value

    @property
    def dist_to_origin(self) -> float:
        return self._vector.magnitude

    def __copy__(self) -> Point:
        return type(self)(self.x, self.y)


@dataclass
class Style:
    stroke_color: Color | None = Color.green
    stroke_width: int = 1
    fill_color: Color | None = None


class Shape(ABC):
    style: Style

    _on_draw_path: OnDrawPathCallback

    def __init__(self, on_draw_path: OnDrawPathCallback, *, style: Style | None) -> None:
        self._on_draw_path = on_draw_path
        self.style = style or Style()

    @abstractmethod
    def as_path(self) -> Path: ...

    def draw(self) -> None:
        self._on_draw_path(self.as_path())

    @abstractmethod
    def __copy__(self): ...


class Path(Shape):

    @dataclass(frozen=True)
    class MoveTo:
        x: float
        y: float

    @dataclass(frozen=True)
    class LineTo:
        x: float
        y: float

    @dataclass(frozen=True)
    class Close:
        pass

    Action: ClassVar = MoveTo | LineTo | Close

    _actions: list[Action]

    def __init__(
            self,
            on_draw_path: OnDrawPathCallback,
            actions: Iterable[Action] | None = None,
            *,
            style: Style | None = None,
    ) -> None:
        super().__init__(on_draw_path, style=style)

        self._actions = []
        # We populate _actions using the public property setter @actions.setter
        if actions is not None:
            self.actions = actions

    @property
    def actions(self) -> list[Action]:
        """A copy of the actions that have thus far been added to the path."""
        # We return a copy to prevent internal state from be unintentionally
        # mutated externally.
        return self._copy_actions()

    @actions.setter
    def actions(self, actions: Iterable[Action]) -> None:
        self._actions = list(actions)

    def add_action(self, action: Action, *extra_actions: Action) -> Path:
        self._actions.append(action)
        self._actions.extend(list(extra_actions))

        return self

    def move_to(self, x: float, y: float) -> Path:
        return self.add_action(self.MoveTo(x=x, y=y))

    def line_to(self, x: float, y: float) -> Path:
        return self.add_action(self.LineTo(x=x, y=y))

    def close(self) -> Path:
        return self.add_action(self.Close())

    def as_path(self) -> Path:
        return copy(self)

    def __copy__(self) -> Path:
        return type(self)(self._on_draw_path, self._copy_actions(), style=self.style)

    def _copy_actions(self) -> list[Action]:
        return [copy(action) for action in self._actions]


OnDrawPathCallback = Callable[[Path], None]


class Polygon(Shape):
    _points: list[Point]

    def __init__(
            self,
            on_draw_path: OnDrawPathCallback,
            points: Iterable[Point] | None = None,
            *,
            style: Style | None = None,
    ) -> None:
        super().__init__(on_draw_path, style=style)

        self._points = []
        if points is not None:
            # We populate _vertices using the public property setter @points.setter
            self.points = points

    @property
    def points(self) -> list[Point]:
        """A copy of the vertices that have thus far been added to the polygon."""
        # We return a copy to prevent internal state from be unintentionally
        # mutated externally.
        return self._copy_points()

    @points.setter
    def points(self, points: Iterable[Point]) -> None:
        self.points = list(points)

    def add_point(self, point: Point, *extra_points: Point) -> Polygon:
        self.points.append(point)
        self.points.extend(list(extra_points))

        return self

    def as_path(self) -> Path:
        path = Path(self._on_draw_path, style=self.style)

        try:
            path.move_to(self._points[0].x, self._points[0].y)
        except IndexError:
            return path

        try:
            for point in self.points[1:]:
                path.line_to(point.x, point.y)

            path.close()
        except IndexError:
            return path

    def __copy__(self) -> Polygon:
        return type(self)(self._on_draw_path, self._copy_points(), style=self.style)

    def _copy_points(self) -> list[Point]:
        return [copy(point) for point in self._points]


class Rect(Shape):
    _origin: Vector
    _extent: Vector

    def __init__(
            self,
            on_draw_path: OnDrawPathCallback,
            x: float,
            y: float,
            width: float,
            height: float,
            *,
            style: Style | None = None,
    ) -> None:
        super().__init__(on_draw_path, style=style)

        self._origin = Vector(x, y)
        self._extent = Vector(width, height)

    @property
    def origin_x(self) -> float:
        return self._origin.x

    @origin_x.setter
    def origin_x(self, value: float) -> None:
        self._origin.x = value

    @property
    def origin_y(self) -> float:
        return self._origin.y

    @origin_y.setter
    def origin_y(self, value: float) -> None:
        self._origin.y = value

    @property
    def width(self) -> float:
        return self._extent.x

    @width.setter
    def width(self, value: float) -> None:
        self._extent.x = value

    @property
    def height(self) -> float:
        return self._extent.y

    @height.setter
    def height(self, value: float) -> None:
        self._extent.y = value

    def as_path(self) -> Path:
        v1 = self._origin
        v2 = self._origin + self._extent

        return Polygon(
            self._on_draw_path,
            [
                Point(v1.x, v1.y),
                Point(v2.x, v1.y),
                Point(v2.x, v2.y),
                Point(v1.x, v2.y)
            ],
            style=self.style
        ).as_path()

    def __copy__(self) -> Rect:
        return type(self)(
            self._on_draw_path,
            self.origin_x,
            self.origin_y,
            self.width,
            self.height,
            style=self.style,
        )
