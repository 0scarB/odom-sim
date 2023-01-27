from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from pydantic.main import BaseModel

app = FastAPI()


app.mount("/sim", StaticFiles(directory="static", html=True), name="static")


api = APIRouter(prefix="/api")


class FloatValueRequest(BaseModel):
    value: float


@api.put("/set_heading")
async def set_heading(request: FloatValueRequest) -> None:
    print(f"heading={request.value}")


@api.put("/set_speed")
async def set_speed(request: FloatValueRequest) -> None:
    print(f"heading={request.value}")


app.include_router(api)
