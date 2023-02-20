from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from . import geometry
from .shapes import Shape


@dataclass(init=False)
class Component:
    name: str
    transformation: geometry.AffineTransformation
    _shapes: dict[str, Shape]
    _children: dict[str, Component]

    def __init__(
            self,
            *,
            name: str = "root",
            children: dict[str, Component] | None = None,
            **shapes: Shape,
    ) -> None:
        self.name = name
        self.transformation = geometry.AffineTransformation()
        self._shapes = {}
        self._children = {}

        for shape_name, shape in shapes.items():
            self.add_shape(**{shape_name: shape})

        if children is not None:
            for child_name, child in children.items():
                self.add_child(**{child_name: child})

    def transform(self, transformation: geometry.AffineTransformation) -> Component:
        self.transformation = self.transformation.transform(transformation)

        return self

    def shape_exists(self, shape_name: str) -> bool:
        return shape_name in self._shapes

    def add_shape(self, **shapes: Shape) -> Component:
        for shape_name, shape in shapes.items():
            if self.shape_exists(shape_name):
                raise KeyError(
                    f"Shape '{shape_name}' already exists in component '{self.name}'"
                )

            self._shapes[shape_name] = shape

        return self

    def update_shape(self, **shapes: Shape) -> Component:
        for shape_name, shape in shapes.items():
            if not self.shape_exists(shape_name):
                raise KeyError(
                    f"Shape '{shape_name}' does not exist in component '{self.name}'"
                )

            self._shapes[shape_name] = shape

        return self

    def get_shape(self, name: str) -> Shape:
        return self._shapes[name]

    def child_exists(self, child_name: str) -> bool:
        return child_name in self._children

    def add_child(self, **children: Component) -> Component:
        for child_name, child in children.items():
            if child.name == "root":
                child.name = child_name

            if self.child_exists(child_name):
                raise KeyError(
                    f"Child '{child_name}' already exists in component '{self.name}'"
                )

            self._children[child_name] = child

        return self

    def update_child(self, **children: Component) -> Component:
        for child_name, child in children.items():
            if child.name == "root":
                child.name = child_name

            if not self.child_exists(child_name):
                raise KeyError(
                    f"Child '{child_name}' does not exist in component '{self.name}'"
                )

            self._children[child_name] = child

        return self

    def get_child(self, name: str) -> Component:
        return self._children[name]

    def iter_children(self) -> Iterable[Component]:
        return self._children.values()

    def shapes_in_world_coordinates(self) -> Iterable[Shape]:
        for shape in self._shapes.values():
            yield geometry.transform(shape, self.transformation)

        for child in self.iter_children():
            for shape in child.shapes_in_world_coordinates():
                yield geometry.transform(shape, self.transformation)
