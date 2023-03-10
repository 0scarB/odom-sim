import asyncio
from pathlib import Path
from typing import Literal, Callable

from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic.main import BaseModel
import uvicorn


app = FastAPI()

origins = [
    "http://127.0.0.1:*",
    "http://192.168.*.*",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/sim", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")


api = APIRouter(prefix="/api")


class FloatValueRequest(BaseModel):
    value: float


_on_change_steering_angle_callbacks: list[Callable[[float], None]] = []
_on_change_speed_callbacks: list[Callable[[float], None]] = []


def on_change_steering_angle(callback: Callable[[float], None]) -> None:
    _on_change_steering_angle_callbacks.append(callback)


def on_change_speed(callback: Callable[[float], None]) -> None:
    _on_change_speed_callbacks.append(callback)


@api.put("/set_steering_angle")
async def _set_steering_angle(request: FloatValueRequest) -> None:
    for callback in _on_change_steering_angle_callbacks:
        callback(request.value)


@api.put("/set_speed")
async def _set_speed(request: FloatValueRequest) -> None:
    for callback in _on_change_speed_callbacks:
        callback(request.value)


app.include_router(api)


def start_server(
        log_level: Literal["info"] = "info",
) -> None:

    class CustomServer(uvicorn.Server):

        def run(self, sockets=None) -> asyncio.Task:
            self.config.setup_event_loop()
            loop = asyncio.get_event_loop()
            return loop.create_task(self.serve(sockets=sockets))

    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level=log_level, loop="asyncio")
    server = CustomServer(config=config)

    loop = asyncio.get_event_loop()

    if loop.is_running():
        asyncio.wait(server.run())
    else:
        loop.run_until_complete(server.run())
