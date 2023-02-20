import math
import sys
from dataclasses import dataclass

from . import geometry


_LARGE_VALUE = sys.float_info.max


@dataclass
class Odometry:
    translation_x: float
    translation_y: float
    rotation: float


def calculate_next_odometry(
        last_odometry: Odometry,
        *,
        time_elapsed_since_last_odometry_measurement: float,
        speed: float,
        wheel_base: float,
        steering_angle: float,
) -> Odometry:
    turning_radius = wheel_base / math.sin(steering_angle) if steering_angle != 0 else _LARGE_VALUE
    change_in_rotation = speed * time_elapsed_since_last_odometry_measurement / turning_radius
    change_in_position_relative_to_robot = geometry.Vector2d(
        turning_radius * (1 - math.cos(change_in_rotation)),
        turning_radius * math.sin(change_in_rotation)
    )
    change_in_position = geometry.transform(
        change_in_position_relative_to_robot,
        geometry.rotate(last_odometry.rotation)
    )

    odom = Odometry(
        translation_x=last_odometry.translation_x + change_in_position.x,
        translation_y=last_odometry.translation_y + change_in_position.y,
        rotation=last_odometry.rotation + change_in_rotation,
    )

    return odom