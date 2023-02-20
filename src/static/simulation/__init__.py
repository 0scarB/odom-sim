from __future__ import annotations

import math
from dataclasses import dataclass
from typing import cast

from .calculation import Odometry, calculate_next_odometry
from . import geometry
from .component import Component
from .robot import RobotMeasurements, Robot
from . import shapes
from .shapes import Shape


@dataclass
class SimulationParameters:
    robot_measurements: RobotMeasurements = RobotMeasurements(
        wheel_base=0.2,
        track_width=0.2,
        wheel_width=0.03,
        wheel_diameter=0.06,
    )
    min_robot_speed: float = -0.4
    max_robot_speed: float = 0.4
    default_robot_speed: float = 0.4
    min_robot_steering_angle: float = -math.pi / 4
    max_robot_steering_angle: float = math.pi / 4
    min_robot_turning_speed: float = -60 * math.pi / 180
    max_robot_turning_speed: float = 60 * math.pi / 180
    default_robot_turning_speed: float = 60 * math.pi / 180


class Simulation(Component):

    def __init__(self, parameters: SimulationParameters = SimulationParameters()) -> None:
        super().__init__(
            children={
                "robot": Robot(parameters.robot_measurements)
            }
        )

        self._parameters = parameters
        self._robot_speed: float = 0
        self._robot_turning_speed: float = 0
        self._odometry = Odometry(
            translation_x=0,
            translation_y=0,
            rotation=math.pi,
        )

    def move_forward_in_time(self, change_in_time: float) -> Simulation:
        if change_in_time < 0:
            raise _BelowLowerBound

        self.set_bounded_robot_steering_angle(
            self.robot_steering_angle + self.robot_turning_speed * change_in_time
        )
        self._odometry = calculate_next_odometry(
            self._odometry,
            time_elapsed_since_last_odometry_measurement=change_in_time,
            speed=self.robot_speed,
            wheel_base=self._parameters.robot_measurements.wheel_base,
            steering_angle=self.robot_steering_angle
        )
        self._robot.translation = geometry.Vector2d(self._odometry.translation_x, self._odometry.translation_y)
        self._robot.rotation = self._odometry.rotation

        return self

    def start_moving_robot_forward(self, speed: float | None = None) -> Simulation:
        if speed is None:
            speed = self._parameters.default_robot_speed

        if speed < 0:
            raise _BelowLowerBound

        self.robot_speed = speed

        return self

    def start_moving_robot_backward(self, speed: float | None = None) -> Simulation:
        if speed is None:
            speed = self._parameters.default_robot_speed

        if speed < 0:
            raise _BelowLowerBound

        self.robot_speed = -speed

        return self

    def stop_moving_robot(self) -> Simulation:
        self.robot_speed = 0

        return self

    def start_turning_robot_clockwise(self, change_in_angle_per_unit_time: float | None = None) -> Simulation:
        if change_in_angle_per_unit_time is None:
            change_in_angle_per_unit_time = self._parameters.default_robot_turning_speed

        if change_in_angle_per_unit_time < 0:
            raise _BelowLowerBound

        self.robot_turning_speed = change_in_angle_per_unit_time

        return self

    def start_turning_robot_counterclockwise(self, change_in_angle_per_unit_time: float | None = None) -> Simulation:
        if change_in_angle_per_unit_time is None:
            change_in_angle_per_unit_time = self._parameters.default_robot_turning_speed

        if change_in_angle_per_unit_time < 0:
            raise _BelowLowerBound

        self.robot_turning_speed = -change_in_angle_per_unit_time

        return self

    def stop_turning_robot(self) -> Simulation:
        self.robot_turning_speed = 0

        return self

    def set_bounded_robot_speed(self, unbounded_speed: float) -> Simulation:
        try:
            self.robot_speed = unbounded_speed
        except _BelowLowerBound:
            self.robot_speed = self._parameters.min_robot_speed
        except _AboveUpperBound:
            self._robot_speed = self._parameters.max_robot_speed

        return self

    def set_bounded_robot_steering_angle(self, unbounded_angle: float) -> Simulation:
        try:
            self.robot_steering_angle = unbounded_angle
        except _BelowLowerBound:
            self.robot_steering_angle = self._parameters.min_robot_steering_angle
        except _AboveUpperBound:
            self.robot_steering_angle = self._parameters.max_robot_steering_angle

        return self

    def set_bounded_robot_turning_speed(self, unbounded_change_in_angle_per_unit_time: float) -> Simulation:
        try:
            self._robot_turning_speed = unbounded_change_in_angle_per_unit_time
        except _BelowLowerBound:
            self._robot_turning_speed = self._parameters.min_robot_turning_speed
        except _AboveUpperBound:
            self._robot_turning_speed = self._parameters.max_robot_turning_speed

        return self

    @property
    def robot_speed(self) -> float:
        return self._robot_speed

    @robot_speed.setter
    def robot_speed(self, speed: float) -> None:
        if speed < self._parameters.min_robot_speed:
            raise _BelowLowerBound

        if speed > self._parameters.max_robot_speed:
            raise _AboveUpperBound

        self._robot_speed = speed

    @property
    def robot_steering_angle(self) -> float:
        return self._robot.steering_angle

    @robot_steering_angle.setter
    def robot_steering_angle(self, angle: float) -> None:
        if angle < self._parameters.min_robot_steering_angle:
            raise _BelowLowerBound

        if angle > self._parameters.max_robot_steering_angle:
            raise _AboveUpperBound

        self._robot.steering_angle = angle

    @property
    def robot_turning_speed(self) -> float:
        return self._robot_turning_speed

    @robot_turning_speed.setter
    def robot_turning_speed(self, change_in_angle_per_unit_time: float) -> None:
        if change_in_angle_per_unit_time < self._parameters.min_robot_turning_speed:
            raise _BelowLowerBound

        if change_in_angle_per_unit_time > self._parameters.max_robot_turning_speed:
            raise _AboveUpperBound

        self._robot_turning_speed = change_in_angle_per_unit_time

    @property
    def odometry(self) -> Odometry:
        return self._odometry

    @property
    def _robot(self) -> Robot:
        return cast(Robot, self.get_child("robot"))

    @_robot.setter
    def _robot(self, new_robot: Robot) -> None:
        self.update_child(robot=new_robot)


class _BelowLowerBound(ValueError):
    pass


class _AboveUpperBound(ValueError):
    pass
