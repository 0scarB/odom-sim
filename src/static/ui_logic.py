from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from js import document, setInterval
from pyodide.http import pyfetch, FetchResponse
from pyodide.ffi import create_proxy

from simulation import Simulation
from simulation import geometry
from simulation import Shape
from simulation import Component


PIXELS_PER_SIMULATION_UNIT_MEASURE = 500


def main():
    canvas = document.getElementById("canvas")
    canvas_ctx = canvas.getContext("2d")

    update_feq_in_seconds = 20 / 1000

    body = document.getElementsByTagName("body")[0]
    canvas.width = body.clientWidth
    canvas.height = body.clientHeight

    simulation = Simulation().transform(
        geometry
        .scale(PIXELS_PER_SIMULATION_UNIT_MEASURE)
        .translate(canvas.width / 2, canvas.height / 2)
    )

    api = APILayer()

    def handle_forward_key_down() -> None:
        simulation.start_moving_robot_forward()

        api.put_speed(simulation.robot_speed)

    def handle_forward_key_up() -> None:
        simulation.stop_moving_robot()

        api.put_speed(simulation.robot_speed)

    def handle_backward_key_down() -> None:
        simulation.start_moving_robot_backward()

        api.put_speed(simulation.robot_speed)

    def handle_backward_key_up() -> None:
        simulation.stop_moving_robot()

        api.put_speed(simulation.robot_speed)

    def handle_left_key_down() -> None:
        simulation.start_turning_robot_counterclockwise()

        api.put_steering_angle(simulation.robot_steering_angle)

    def handle_left_key_up() -> None:
        simulation.stop_moving_robot()

        api.put_steering_angle(simulation.robot_steering_angle)

    def handle_right_key_down() -> None:
        simulation.start_turning_robot_clockwise()

        api.put_steering_angle(simulation.robot_steering_angle)

    def handle_right_key_up() -> None:
        simulation.stop_turning_robot()

        api.put_steering_angle(simulation.robot_steering_angle)

    KeyboardInputHandler() \
        .on_forward_key_down(handle_forward_key_down) \
        .on_forward_key_up(handle_forward_key_up) \
        .on_backward_key_down(handle_backward_key_down) \
        .on_backward_key_up(handle_backward_key_up) \
        .on_left_key_down(handle_left_key_down) \
        .on_left_key_up(handle_left_key_up) \
        .on_right_key_down(handle_right_key_down) \
        .on_right_key_up(handle_right_key_up)

    def update() -> None:
        simulation.move_forward_in_time(update_feq_in_seconds)

        clear_canvas(canvas, canvas_ctx)
        draw_component(canvas_ctx, simulation)

    update_sim_proxy = create_proxy(update)
    setInterval(update_sim_proxy, update_feq_in_seconds * 1000)


def draw_component(canvas_ctx, component: Component) -> None:
    for shape in component.shapes_in_world_coordinates():
        draw_shape(canvas_ctx, shape)


def draw_shape(canvas_ctx, shape: Shape) -> None:
    canvas_ctx.beginPath()

    canvas_ctx.moveTo(shape.vertices[0].x, shape.vertices[0].y)
    for vertex in shape.vertices[1:]:
        canvas_ctx.lineTo(vertex.x, vertex.y)
    canvas_ctx.closePath()

    if shape.style.stroke_color is not None:
        canvas_ctx.strokeStyle = shape.style.stroke_color
    if shape.style.fill_color is not None:
        canvas_ctx.fillStyle = shape.style.fill_color

    canvas_ctx.fill()
    canvas_ctx.stroke()


def clear_canvas(canvas, canvas_ctx) -> None:
    canvas_ctx.clearRect(0, 0, canvas.width, canvas.height)


class KeyboardInputHandler:

    def __init__(self):
        self.on_key_down_callbacks: list[Callable[[str], None]] = []
        self.on_key_up_callbacks: list[Callable[[str], None]] = []

        document.addEventListener("keydown", create_proxy(self.handle_key_down))
        document.addEventListener("keyup", create_proxy(self.handle_key_up))

    def on_forward_key_down(self, callback: Callable[[str], None] | Callable[[], None]) -> KeyboardInputHandler:
        return self.on_key_down(callback, "w", "ArrowUp", ignore_case=True)

    def on_forward_key_up(self, callback: Callable[[str], None] | Callable[[], None]) -> KeyboardInputHandler:
        return self.on_key_up(callback, "w", "ArrowUp", ignore_case=True)

    def on_backward_key_down(self, callback: Callable[[str], None] | Callable[[], None]) -> KeyboardInputHandler:
        return self.on_key_down(callback, "s", "ArrowDown", ignore_case=True)

    def on_backward_key_up(self, callback: Callable[[str], None] | Callable[[], None]) -> KeyboardInputHandler:
        return self.on_key_up(callback, "s", "ArrowDown", ignore_case=True)

    def on_left_key_down(self, callback: Callable[[str], None] | Callable[[], None]) -> KeyboardInputHandler:
        return self.on_key_down(callback, "a", "ArrowLeft", ignore_case=True)

    def on_left_key_up(self, callback: Callable[[str], None] | Callable[[], None]) -> KeyboardInputHandler:
        return self.on_key_up(callback, "a", "ArrowLeft", ignore_case=True)

    def on_right_key_down(self, callback: Callable[[str], None] | Callable[[], None]) -> KeyboardInputHandler:
        return self.on_key_down(callback, "d", "ArrowRight", ignore_case=True)

    def on_right_key_up(self, callback: Callable[[str], None] | Callable[[], None]) -> KeyboardInputHandler:
        return self.on_key_up(callback, "d", "ArrowRight", ignore_case=True)

    def on_key_down(
            self,
            callback: Callable[[str], None] | Callable[[], None],
            *expected_keys: str,
            ignore_case: bool = False
    ) -> KeyboardInputHandler:
        return self.add_key_callback_to_list(
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
    ) -> KeyboardInputHandler:
        return self.add_key_callback_to_list(
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
    ) -> KeyboardInputHandler:

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

        return self


@dataclass
class Request:
    route: str
    method: str = "GET"
    body: str | None = None
    headers: dict[str, str] | None = None


class APILayer:
    API_BASE_URL = "http://0.0.0.0:8000/api"

    def __init__(self) -> None:
        self._async_tasks: deque[asyncio.Task] = deque()

    def put_steering_angle(self, heading: float) -> None:
        self._create_request_task(Request(
            route="/set_steering_angle",
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


main()
