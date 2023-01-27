from . import on_change_heading, on_change_speed, start_server


if __name__ == "__main__":
    on_change_heading(lambda heading: print(f"Changed heading to {heading}"))
    on_change_speed(lambda speed: print(f"Changed speed to {speed}"))
    start_server()
