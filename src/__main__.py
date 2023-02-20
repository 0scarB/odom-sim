from . import on_change_steering_angle, on_change_speed, start_server


if __name__ == "__main__":
    on_change_steering_angle(lambda angle: print(f"Changed steering angle to {angle}"))
    on_change_speed(lambda speed: print(f"Changed speed to {speed}"))
    start_server()
