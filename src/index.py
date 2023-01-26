from js import document, setInterval
from pyodide import create_proxy


def main():
    canvas = document.getElementById("canvas")
    ctx = canvas.getContext("2d")

    draw_frame_proxy = create_proxy(draw_frame)

    setInterval(draw_frame_proxy, 10, ctx)


class Sim:
    heading: float = 0
    speed: float = 0

    def __init__(self):



main()