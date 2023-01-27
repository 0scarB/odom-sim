from __future__ import annotations

import asyncio
from asyncio import Task
import math
from collections import deque
from collections.abc import Callable
import sys
from dataclasses import dataclass
from typing import Any

from js import document, setInterval
from pyodide.http import pyfetch, FetchResponse
from pyodide.ffi import create_proxy


def main():
    canvas = document.getElementById("canvas")
    ctx = canvas.getContext("2d")

    update_feq_in_seconds = 20 / 1000

    sim = Sim(canvas, ctx, update_feq_in_seconds)

    update_sim_proxy = create_proxy(sim.update)

    setInterval(update_sim_proxy, update_feq_in_seconds * 1000)


class Sim:

    def __init__(self, canvas, canvas_ctx, update_feq_in_seconds: float):
        self.canvas = canvas
        self.canvas_ctx = canvas_ctx
        self.update_feq_in_seconds = update_feq_in_seconds

        self.keyboard_input_handler = KeyboardInputHandler()
        self.api_layer = APILayer()
        self.robot = Robot(canvas_ctx, self.keyboard_input_handler, self.update_feq_in_seconds, self.api_layer)

    def update(self) -> None:
        self.clear_canvas()

        self.robot.update()
        self.api_layer.wait_for_requests_to_finish()

    def clear_canvas(self) -> None:
        self.canvas_ctx.clearRect(0, 0, self.canvas.width, self.canvas.height)


class Robot:
    LENGTH = 0.2
    WHEEL_BASE = 0.2
    WHEEL_WIDTH = 0.03
    WHEEL_DIAMETER = 0.06
    ROD_THICKNESS = WHEEL_BASE / 20
    HEADING_INCREMENT = 0.01
    MAX_HEADING_CHANGE = math.pi / 4
    MOVEMENT_SPEED = 1 / 5

    def __init__(
            self,
            canvas_ctx,
            keyboard_input_handler: KeyboardInputHandler,
            update_feq_in_seconds: float,
            api_layer: APILayer,
            x_in_pixels: float | None = None,
            y_in_pixels: float | None = None,
            pixels_per_meter: float = 500,
    ):
        self.canvas_ctx = canvas_ctx
        self.pixels_per_meter = pixels_per_meter
        self.update_interval_in_seconds = update_feq_in_seconds
        self.api_layer = api_layer

        self._heading = 0
        self._speed = 0

        self.is_moving_right = False
        self.is_moving_left = False
        self.x = (x_in_pixels / self.pixels_per_meter if x_in_pixels else self.WHEEL_BASE / 2) + 0.1
        self.y = (y_in_pixels / self.pixels_per_meter if y_in_pixels else self.LENGTH / 2) + 0.1
        self.rot = math.pi

        def on_right_key_down():
            self.is_moving_right = True

        def on_left_key_down():
            self.is_moving_left = True

        def on_steering_key_up():
            self.is_moving_left = False
            self.is_moving_right = False

        def on_forward_key_down():
            self.speed = self.MOVEMENT_SPEED

        def on_backward_key_down():
            self.speed = -self.MOVEMENT_SPEED

        def on_movement_key_up():
            self.speed = 0

        keyboard_input_handler.on_left_key_down(on_left_key_down)
        keyboard_input_handler.on_right_key_down(on_right_key_down)
        keyboard_input_handler.on_left_key_up(on_steering_key_up)
        keyboard_input_handler.on_right_key_up(on_steering_key_up)
        keyboard_input_handler.on_forward_key_down(on_forward_key_down)
        keyboard_input_handler.on_backward_key_down(on_backward_key_down)
        keyboard_input_handler.on_forward_key_up(on_movement_key_up)
        keyboard_input_handler.on_backward_key_up(on_movement_key_up)

    @property
    def heading(self) -> float:
        return self._heading

    @heading.setter
    def heading(self, value: float) -> None:
        self._heading = value
        self.api_layer.put_heading(value)

    @property
    def speed(self) -> float:
        return self._speed

    @speed.setter
    def speed(self, value: float) -> None:
        self._speed = value
        self.api_layer.put_heading(value)

    def update(self) -> None:
        self.update_heading()
        self.update_position_and_rotation()

        self.draw_rect(
            -self.ROD_THICKNESS / 2, -self.LENGTH / 2,
            self.ROD_THICKNESS, self.LENGTH,
            0
        )

        self.draw_axel(-self.LENGTH / 2, 0)
        self.draw_axel(self.LENGTH / 2, self.heading)
        self.draw_arrow_around_center(
            0, self.ROD_THICKNESS + (self.LENGTH / 2) + 0.01,
            self.ROD_THICKNESS, self.LENGTH / 4,
            self.heading
        )
        self.draw_turing_circle()

    def update_heading(self) -> None:
        if self.is_moving_left:
            self.increment_heading(direction=-1)

        if self.is_moving_right:
            self.increment_heading(direction=1)
            
    def update_position_and_rotation(self) -> None:
        cx, cy, r = self.get_turning_circle()

        angle_change_on_turning_circle = self.speed * self.update_interval_in_seconds / r

        change_in_x, change_in_y = rotate_around_point(cx, cy, 0, 0, -angle_change_on_turning_circle)
        self.x, self.y = translate(self.x, self.y, *rotate_around_origin(change_in_x, change_in_y, self.rot))
        self.rot -= angle_change_on_turning_circle
            
    def get_turning_circle(self) -> tuple[float, float, float]:
        line1_x1, line1_y1 = 0, -self.LENGTH / 2
        line1_x2, line1_y2 = 1, -self.LENGTH / 2

        line2_x1, line2_y1 = 0, self.LENGTH / 2
        line2_x2, line2_y2 = translate(*rotate_around_origin(1, 0, self.heading), 0, self.LENGTH / 2)

        try:
            cx, cy = line_intersection(
                ((line1_x1, line1_y1), (line1_x2, line1_y2)),
                ((line2_x1, line2_y1), (line2_x2, line2_y2)),
            )
        except ValueError:
            return sys.float_info.max, -self.LENGTH / 2, sys.float_info.max

        r = get_dist(cx, cy, 0, 0)
        if cx < 0:
            r = -r

        return cx, cy, r

    def increment_heading(self, direction: float) -> None:
        new_heading = self.heading + direction * self.HEADING_INCREMENT

        new_heading = max(new_heading, -self.MAX_HEADING_CHANGE)
        new_heading = min(new_heading, self.MAX_HEADING_CHANGE)

        self.heading = new_heading

    def draw_rect(
            self,
            x: float,
            y: float,
            width: float,
            height: float,
            rel_rot: float,
    ) -> None:
        x_min = x
        y_min = y
        x_max = x + width
        y_max = y + height

        c = ((x_min + x_max) / 2, (y_min + y_max) / 2)

        p1 = (x_min, y_min)
        p2 = (x_max, y_min)
        p3 = (x_max, y_max)
        p4 = (x_min, y_max)

        self.canvas_ctx.beginPath()
        is_first_point = True
        for p in (p1, p2, p3, p4):
            canvas_p = rotate_around_point(c[0], c[1], p[0], p[1], rel_rot)
            canvas_p = translate(canvas_p[0], canvas_p[1], self.x, self.y)
            canvas_p = rotate_around_point(self.x, self.y, canvas_p[0], canvas_p[1], self.rot)
            canvas_p = scale_from_origin(canvas_p[0], canvas_p[1], self.pixels_per_meter)

            if is_first_point:
                self.canvas_ctx.moveTo(canvas_p[0], canvas_p[1])
                is_first_point = False
            else:
                self.canvas_ctx.lineTo(canvas_p[0], canvas_p[1])

        self.canvas_ctx.closePath()
        self.canvas_ctx.strokeStyle = "green"
        self.canvas_ctx.stroke()

    def draw_arrow_around_center(
            self,
            x: float,
            y: float,
            width: float,
            height: float,
            rel_rot: float,
    ) -> None:
        x_centered = x - width / 2
        y_centered = y - width / 2

        x_min = x_centered
        y_min = y_centered
        x_max = x_centered + width
        x_mid = (x_min + x_max) / 2
        y_max = y_centered + height

        c = ((x_min + x_max) / 2, (y_min + y_max) / 2)

        p1 = (x_min, y_min)
        p2 = (x_min, y_max)
        p3 = (x_min - 0.02, y_max)
        p4 = (x_mid, y_max + 0.04)
        p5 = (x_max + 0.02, y_max)
        p6 = (x_max, y_max)
        p7 = (x_max, y_min)

        self.canvas_ctx.beginPath()
        is_first_point = True
        for p in (p1, p2, p3, p4, p5, p6, p7):
            canvas_p = rotate_around_point(c[0], c[1], p[0], p[1], rel_rot)
            canvas_p = translate(canvas_p[0], canvas_p[1], self.x, self.y)
            canvas_p = rotate_around_point(self.x, self.y, canvas_p[0], canvas_p[1], self.rot)
            canvas_p = scale_from_origin(canvas_p[0], canvas_p[1], self.pixels_per_meter)

            if is_first_point:
                self.canvas_ctx.moveTo(canvas_p[0], canvas_p[1])
                is_first_point = False
            else:
                self.canvas_ctx.lineTo(canvas_p[0], canvas_p[1])

        self.canvas_ctx.closePath()
        self.canvas_ctx.strokeStyle = "green"
        self.canvas_ctx.stroke()

    def draw_rect_around_center(
            self,
            x: float,
            y: float,
            width: float,
            height: float,
            rel_rot: float,
    ) -> None:
        self.draw_rect(x - width / 2, y - height / 2, width, height, rel_rot)

    def draw_axel(self, offset: float, heading: float) -> None:
        self.draw_rect(
            -self.WHEEL_BASE / 2, -self.ROD_THICKNESS / 2 + offset,
            self.WHEEL_BASE, self.ROD_THICKNESS,
            0
        )

        self.draw_wheel(-self.WHEEL_BASE / 2, offset, heading)
        self.draw_wheel(self.WHEEL_BASE / 2, offset, heading)

    def draw_wheel(self, x: float, y: float, heading: float) -> None:
        self.draw_rect(
            x - self.WHEEL_WIDTH / 2,
            y - self.WHEEL_DIAMETER / 2,
            self.WHEEL_WIDTH,
            self.WHEEL_DIAMETER,
            heading,
        )

    def draw_turing_circle(self) -> None:
        line1_x1, line1_y1 = 0, -self.LENGTH / 2
        line1_x2, line1_y2 = 1, -self.LENGTH / 2

        line2_x1, line2_y1 = 0, self.LENGTH / 2
        line2_x2, line2_y2 = translate(*rotate_around_origin(1, 0, self.heading), 0, self.LENGTH / 2)

        self.draw_line(line1_x1, line1_y1, line1_x2, line1_y2)
        self.draw_line(line2_x1, line2_y1, line2_x2, line2_y2)

        try:
            cx, cy = line_intersection(
                ((line1_x1, line1_y1), (line1_x2, line1_y2)),
                ((line2_x1, line2_y1), (line2_x2, line2_y2)),
            )
        except ValueError:
            return

        r = get_dist(cx, cy, 0, 0)

        self.canvas_ctx.beginPath()
        self.canvas_ctx.arc(*self.robot_point_to_canvas_point(cx, cy), r * self.pixels_per_meter, 0, 2 * math.pi, False)
        self.canvas_ctx.strokeStyle = "blue"
        self.canvas_ctx.stroke()

    def draw_line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.canvas_ctx.beginPath()
        self.canvas_ctx.moveTo(*self.robot_point_to_canvas_point(x1, y1))
        self.canvas_ctx.lineTo(*self.robot_point_to_canvas_point(x2, y2))
        self.canvas_ctx.strokeStyle = "blue"
        self.canvas_ctx.stroke()

    def robot_point_to_canvas_point(self, x: float, y: float) -> tuple[float, float]:
        x, y = translate(x, y, self.x, self.y)
        x, y = rotate_around_point(self.x, self.y, x, y, self.rot)
        return scale_from_origin(x, y, self.pixels_per_meter)


class KeyboardInputHandler:

    def __init__(self):
        self.on_key_down_callbacks: list[Callable[[str], None]] = []
        self.on_key_up_callbacks: list[Callable[[str], None]] = []

        document.addEventListener("keydown", create_proxy(self.handle_key_down))
        document.addEventListener("keyup", create_proxy(self.handle_key_up))

    def on_forward_key_down(self, callback: Callable[[str], None] | Callable[[], None]) -> None:
        self.on_key_down(callback, "w", "ArrowUp", ignore_case=True)

    def on_forward_key_up(self, callback: Callable[[str], None] | Callable[[], None]) -> None:
        self.on_key_up(callback, "w", "ArrowUp", ignore_case=True)

    def on_backward_key_down(self, callback: Callable[[str], None] | Callable[[], None]) -> None:
        self.on_key_down(callback, "s", "ArrowDown", ignore_case=True)

    def on_backward_key_up(self, callback: Callable[[str], None] | Callable[[], None]) -> None:
        self.on_key_up(callback, "s", "ArrowDown", ignore_case=True)

    def on_left_key_down(self, callback: Callable[[str], None] | Callable[[], None]) -> None:
        self.on_key_down(callback, "a", "ArrowLeft", ignore_case=True)

    def on_left_key_up(self, callback: Callable[[str], None] | Callable[[], None]) -> None:
        self.on_key_up(callback, "a", "ArrowLeft", ignore_case=True)

    def on_right_key_down(self, callback: Callable[[str], None] | Callable[[], None]) -> None:
        self.on_key_down(callback, "d", "ArrowRight", ignore_case=True)

    def on_right_key_up(self, callback: Callable[[str], None] | Callable[[], None]) -> None:
        self.on_key_up(callback, "d", "ArrowRight", ignore_case=True)

    def on_key_down(
            self,
            callback: Callable[[str], None] | Callable[[], None],
            *expected_keys: str,
            ignore_case: bool = False
    ) -> None:
        self.add_key_callback_to_list(
            self.on_key_down_callbacks,
            callback,
            *expected_keys,
            ignore_case=ignore_case,
        )

    def on_key_up(
            self,
            callback: Callable[[str], None] | Callable[[], None],
            *expected_keys: str,
            ignore_case: bool = False
    ) -> None:
        self.add_key_callback_to_list(
            self.on_key_up_callbacks,
            callback,
            *expected_keys,
            ignore_case=ignore_case,
        )

    def handle_key_down(self, event) -> None:
        for callback in self.on_key_down_callbacks:
            callback(event.key)

    def handle_key_up(self, event) -> None:
        for callback in self.on_key_up_callbacks:
            callback(event.key)

    def add_key_callback_to_list(
            self,
            callbacks: list[Callable[[str], None]],
            callback: Callable[[str], None] | Callable[[], None],
            *expected_keys: str,
            ignore_case: bool = False
    ) -> None:

        def try_callback_with_and_without_key_arg(key: str) -> None:
            try:
                return callback(key)
            except TypeError as err:
                if "arguments" in str(err):
                    return callback()

                raise err

        if expected_keys:

            if ignore_case:
                expected_keys_set = {key.lower() for key in expected_keys}
            else:
                expected_keys_set = set(expected_keys)

            def real_callback(key: str) -> None:

                if ignore_case:
                    key = key.lower()

                if key in expected_keys_set:
                    try_callback_with_and_without_key_arg(key)

        else:

            def real_callback(key: str) -> None:
                try_callback_with_and_without_key_arg(key)

        callbacks.append(real_callback)


@dataclass
class Request:
    route: str
    method: str = "GET"
    body: str | None = None
    headers: dict[str, str] | None = None


class APILayer:
    API_BASE_URL = "http://127.0.0.1:8000/api"

    def __init__(self) -> None:
        self._async_tasks: deque[asyncio.Task] = deque()

    def put_heading(self, heading: float) -> None:
        self._create_request_task(Request(
            route="/set_heading",
            method="PUT",
            body=r'{"value": ' + str(heading) + r'}',
            headers={"Content-Type": "application/json"}
        ))

    def put_speed(self, speed: float) -> None:
        self._create_request_task(Request(
            route="/set_speed",
            method="PUT",
            body=r'{"value": ' + str(speed) + r'}',
            headers={"Content-Type": "application/json"}
        ))

    def wait_for_requests_to_finish(self) -> None:
        loop = asyncio.get_event_loop()

        while self._async_tasks:
            task = self._async_tasks.popleft()
            loop.run_until_complete(task)

    def _create_request_task(self, request: Request) -> None:
        self._async_tasks.append(asyncio.create_task(self._make_request(request)))

    async def _make_request(self, request: Request, **fetch_kwargs: Any) -> FetchResponse:
        kwargs = {"method": request.method, "mode": "cors"}
        if request.body and request.method not in ["GET", "HEAD"]:
            kwargs["body"] = request.body
        if request.headers:
            kwargs["headers"] = request.headers
        kwargs.update(fetch_kwargs)

        response = await pyfetch(f"{self.API_BASE_URL}{request.route}", **kwargs)
        return response


def translate(x: float, y: float, x_offset: float, y_offset: float) -> tuple[float, float]:
    return (
        x + x_offset,
        y + y_offset,
    )


def rotate_around_origin(
        x: float,
        y: float,
        angle: float,
) -> tuple[float, float]:
    return (
        x * math.cos(angle) - y * math.sin(angle),
        x * math.sin(angle) + y * math.cos(angle),
    )


def rotate_around_point(ref_x: float, ref_y: float, x: float, y: float, angle: float) -> tuple[float, float]:
    return apply_transformation_using_reference_point_as_origin(
        ref_x,
        ref_y,
        rotate_around_origin,
        x,
        y,
        angle,
    )


def scale_from_origin(x: float, y: float, factor: float) -> tuple[float, float]:
    return (
        x * factor,
        y * factor
    )


def scale_from_point(ref_x: float, ref_y: float, x: float, y: float, factor: float) -> tuple[float, float]:
    return apply_transformation_using_reference_point_as_origin(
        ref_x,
        ref_y,
        scale_from_origin,
        x,
        y,
        factor,
    )


def apply_transformation_using_reference_point_as_origin(
        ref_x: float,
        ref_y: float,
        transformation: Callable[[float, float, ...], tuple[float, float]],
        x: float,
        y: float,
        *args: Any,
        **kwargs: Any,
) -> tuple[float, float]:
    x, y = translate(x, y, -ref_x, -ref_y)
    x, y = transformation(x, y, *args, **kwargs)
    return translate(x, y, ref_x, ref_y)


# Source: https://stackoverflow.com/questions/20677795/how-do-i-compute-the-intersection-point-of-two-lines
def get_intersection(
        line1_x1: float,
        line1_y1: float,
        line1_x2: float,
        line1_y2: float,
        line2_x1: float,
        line2_y1: float,
        line2_x2: float,
        line2_y2: float,
) -> tuple[float, float]:
    # xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    # ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    xdiff = (line1_x1 - line1_x2, line2_x1 - line2_x2)
    ydiff = (line1_y1 - line1_y2, line2_y1 - line2_y2)

    def det(x1, y1, x2, y2):
        return x1 * y2 - y1 * x2

    div = det(*xdiff, *ydiff)
    if div == 0:
        raise ValueError('lines do not intersect')

    d = (det(line1_x1, line1_y1, line1_x2, line1_y2), det(line2_x1, line2_y1, line2_x2, line2_y2))
    x = det(*d, *xdiff) / div
    y = det(*d, *ydiff) / div
    return x, y


def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        raise ValueError('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


def get_dist(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


main()
