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
        self.keyboardInputHandler.on_key_down(lambda k: f"Down {k}")
        self.keyboardInputHandler.on_key_up(lambda k: f"Up {k}")
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

        self.heading = 0
        self.speed = 0
        self.x = x_in_pixels / self.pixels_per_meter if x_in_pixels else self.WHEEL_BASE / 2
        self.y = y_in_pixels / self.pixels_per_meter if y_in_pixels else self.LENGTH / 2
        self.rot = 5 * math.pi / 3

    def draw(self) -> None:
        self.draw_rect(
            -self.ROD_THICKNESS / 2, -self.LENGTH / 2,
            self.ROD_THICKNESS, self.LENGTH,
            0
        )

        self.draw_rect(
            -self.WHEEL_BASE / 2, -self.ROD_THICKNESS / 2 - self.LENGTH / 2,
            self.WHEEL_BASE, self.ROD_THICKNESS,
            0
        )

        self.draw_rect(
            -self.WHEEL_BASE / 2, -self.ROD_THICKNESS / 2 + self.LENGTH / 2,
            self.WHEEL_BASE, self.ROD_THICKNESS,
            0
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


class KeyboardInputHandler:

    def __init__(self):
        self.on_key_down_callbacks: list[Callable[[str], None]] = []
        self.on_key_up_callbacks: list[Callable[[str], None]] = []

        main_el = document.getElementsByTagName("main")[0]
        print(main_el)
        main_el.addEventListener("keydown", self.handle_key_down)
        main_el.addEventListener("keyup", self.handle_key_up)

    def on_key_down(self, callback: Callable[[str], None]) -> None:
        self.on_key_down_callbacks.append(callback)

    def handle_key_down(self, event) -> None:
        for callback in self.on_key_down_callbacks:
            callback(key)

    def on_key_up(self, callback: Callable[[str], None]) -> None:
        self.on_key_up_callbacks.append(callback)

    def handle_key_up(self, event) -> None:
        for callback in self.on_key_up_callbacks:
            callback(key)


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
