from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from . import geometry
from .component import Component
from .shapes import Line, Rect, Vertex, Shape


@dataclass
class RobotMeasurements:
    wheel_base: float
    track_width: float
    wheel_width: float
    wheel_diameter: float


class Robot(Component):

    def __init__(self, measurements: RobotMeasurements, *, steering_angle: float = 0) -> None:
        super().__init__(name="robot")

        self._measurements = measurements
        self._translation = geometry.Vector2d(0, 0)
        self._rotation = 0
        self._steering_angle = 0

        self._update_measurements(measurements)
        self._update_steering_angle(steering_angle)

    @property
    def measurements(self) -> RobotMeasurements:
        return self._measurements

    @measurements.setter
    def measurements(self, measurements: RobotMeasurements) -> None:
        self._update_measurements(measurements)

    @property
    def translation(self) -> geometry.Vector2d:
        return self._translation

    @translation.setter
    def translation(self, vector: geometry.Vector2d) -> None:
        self._translation = vector

        self._update_transformation()

    @property
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, angle: float) -> None:
        self._rotation = angle

        self._update_transformation()

    @property
    def steering_angle(self) -> float:
        return self._steering_angle

    @steering_angle.setter
    def steering_angle(self, angle: float) -> None:
        self._update_steering_angle(angle)

    @property
    def front_axel_linkage(self) -> AxelLinkage:
        return cast(AxelLinkage, self.get_child("front_axel_linkage"))

    @property
    def back_axel_linkage(self) -> AxelLinkage:
        return cast(AxelLinkage, self.get_child("back_axel_linkage"))

    def _update_measurements(self, measurements: RobotMeasurements) -> None:
        front_axel_linkage = AxelLinkage(
            axel_length=measurements.track_width,
            wheel_width=measurements.wheel_width,
            wheel_diameter=measurements.wheel_diameter,
        )
        back_axel_linkage = AxelLinkage(
            axel_length=measurements.track_width,
            wheel_width=measurements.wheel_width,
            wheel_diameter=measurements.wheel_diameter,
        )

        front_axel_linkage.transform(geometry.translate(0, measurements.wheel_base))

        self._add_or_update_children(
            front_axel_linkage=front_axel_linkage,
            back_axel_linkage=back_axel_linkage,
        )
        self._add_or_update_shapes(
            center_rod=Line(
                Vertex(0, 0),
                Vertex(0, measurements.wheel_base)
            )
        )

        self._measurements = measurements
        # Reposition front wheels' angle
        self._update_steering_angle(self._steering_angle)

    def _add_or_update_shapes(self, **shapes: Shape) -> None:
        for shape_name, shape in shapes.items():
            if self.shape_exists(shape_name):
                self.update_shape(**{shape_name: shape})
            else:
                self.add_shape(**{shape_name: shape})

    def _add_or_update_children(self, **children: Component) -> None:
        for child_name, child in children.items():
            if self.child_exists(child_name):
                self.update_child(**{child_name: child})
            else:
                self.add_child(**{child_name: child})

    def _update_transformation(self) -> None:
        self.transformation = geometry.rotate(self._rotation).translate(self._translation)

    def _update_steering_angle(self, angle: float) -> None:
        self.front_axel_linkage.wheel_rotation = angle

        self._steering_angle = angle


class AxelLinkage(Component):

    def __init__(
            self,
            axel_length: float,
            wheel_width: float,
            wheel_diameter: float,
    ) -> None:
        axel_start = Vertex(-axel_length / 2, 0)
        axel_end = Vertex(axel_length / 2, 0)

        left_wheel = Wheel(wheel_width, wheel_diameter)
        right_wheel = Wheel(wheel_width, wheel_diameter)

        left_wheel.transform(geometry.translate(axel_start.x, axel_start.y))
        right_wheel.transform(geometry.translate(axel_end.x, axel_end.y))

        super().__init__(
            axel=Line(axel_start, axel_end),
            children={
                "left_wheel": left_wheel,
                "right_wheel": right_wheel,
            }
        )

    @property
    def left_wheel(self) -> Wheel:
        return cast(Wheel, self.get_child("left_wheel"))

    @property
    def right_wheel(self) -> Wheel:
        return cast(Wheel, self.get_child("right_wheel"))

    @property
    def wheel_rotation(self) -> float:
        return self.left_wheel.rotation

    @wheel_rotation.setter
    def wheel_rotation(self, angle: float) -> None:
        self.left_wheel.rotation = angle
        self.right_wheel.rotation = angle


class Wheel(Component):

    def __init__(self, width: float, diameter: float) -> None:
        self._width = width
        self._diameter = diameter
        self._rotation = 0

        super().__init__(wheel=self._create_shape())

    @property
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, angle: str) -> None:
        self._rotation = angle

        self.update_shape(wheel=self._create_shape())

    def _create_shape(self) -> Shape:
        return geometry.transform(
            Rect(
                Vertex(-self._width / 2, -self._diameter / 2),
                Vertex(self._width, self._diameter)
            ),
            geometry.rotate(self._rotation)
        )
