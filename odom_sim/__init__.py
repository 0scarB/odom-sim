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


_on_change_heading_callbacks: list[Callable[[float], None]] = []
_on_change_speed_callbacks: list[Callable[[float], None]] = []


def on_change_heading(callback: Callable[[float], None]) -> None:
    _on_change_heading_callbacks.append(callback)


def on_change_speed(callback: Callable[[float], None]) -> None:
    _on_change_speed_callbacks.append(callback)


@api.put("/set_heading")
async def _set_heading(request: FloatValueRequest) -> None:
    for callback in _on_change_heading_callbacks:
        callback(request.value)


@api.put("/set_speed")
async def _set_speed(request: FloatValueRequest) -> None:
    for callback in _on_change_speed_callbacks:
        callback(request.value)


app.include_router(api)


def start_server(
        log_level: Literal["info"] = "info",
) -> None:
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level=log_level, loop="asyncio")
    server = uvicorn.Server(config=config)

    asyncio.run(server.run())
