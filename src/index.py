import math
from collections.abc import Callable
from typing import Any

from js import document, setInterval
from pyodide.ffi import create_proxy


def main():
    canvas = document.getElementById("canvas")
    ctx = canvas.getContext("2d")

    sim = Sim(canvas, ctx)

    update_sim_proxy = create_proxy(sim.update)

    setInterval(update_sim_proxy, 20)


class Sim:

    def __init__(self, canvas, canvas_ctx):
        self.canvas = canvas
        self.canvas_ctx = canvas_ctx

        self.keyboardInputHandler = KeyboardInputHandler()
        self.robot = Robot(canvas_ctx)

    def update(self) -> None:
        self.clear_canvas()

        self.robot.draw()

    def clear_canvas(self) -> None:
        self.canvas_ctx.clearRect(0, 0, self.canvas.width, self.canvas.height)


class Robot:
    LENGTH = 0.2
    WHEEL_BASE = 0.2
    WHEEL_WIDTH = 0.03
    WHEEL_DIAMETER = 0.06
    ROD_THICKNESS = WHEEL_BASE / 10

    def __init__(
            self,
            canvas_ctx,
            x_in_pixels: float | None = None,
            y_in_pixels: float | None = None,
            pixels_per_meter: float = 1000,
    ):
        self.canvas_ctx = canvas_ctx
        self.pixels_per_meter = pixels_per_meter

        self.heading = math.pi / 4
        self.speed = 0
        self.x = x_in_pixels / self.pixels_per_meter if x_in_pixels else self.WHEEL_BASE / 2
        self.y = y_in_pixels / self.pixels_per_meter if y_in_pixels else self.LENGTH / 2
        self.rot = 0

    def draw(self) -> None:
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


main()
