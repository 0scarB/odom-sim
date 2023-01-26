from __future__ import annotations

from typing import Any


class _ColorChannel:
    _public_attribute_name: str
    _private_attribute_name: str
    _value: int

    def __init__(self) -> None:
        self._public_attribute_name = ""
        self._private_attribute_name = ""

    def __set_name__(self, owner: Any, name: str) -> None:
        self._public_attribute_name = name
        self._private_attribute_name = f"_{name}"

    def __set__(self, obj: Color, value: int) -> None:
        if not (0 <= value < 256):
            raise ValueError(
                f"Color channel '{self._public_attribute_name}' only accepts values >=0 and <256. "
                f"Received color.{self._public_attribute_name}={value}"
            )

        setattr(obj, self._private_attribute_name, value)

    def __get__(self, obj: Color, obj_type: Any = None) -> int:
        return getattr(obj, self._private_attribute_name)


class Color:
    """Declarative color class in the RGB(A) color space."""

    @property
    @classmethod
    def black(cls) -> Color:
        return cls(0, 0, 0)

    @property
    @classmethod
    def white(cls) -> Color:
        return cls(255, 255, 255)

    @property
    @classmethod
    def red(cls) -> Color:
        return cls(255, 0, 0)

    @property
    @classmethod
    def green(cls) -> Color:
        return cls(0, 255, 0)

    @property
    @classmethod
    def blue(cls) -> Color:
        return cls(0, 0, 255)

    @property
    @classmethod
    def cyan(cls) -> Color:
        return cls.red.compliment

    @property
    @classmethod
    def magenta(cls) -> Color:
        return cls.green.compliment

    @property
    @classmethod
    def yellow(cls) -> Color:
        return cls.blue.compliment

    _r: float
    _g: float
    _b: float
    _a: float

    r = _ColorChannel()
    g = _ColorChannel()
    b = _ColorChannel()
    a = _ColorChannel()

    def __init__(self, r: int, g: int, b: int, a: int = 255) -> None:
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def lighter(self, factor: float, keep_within_bounds: bool = True) -> Color:

        def lighten_channel(value: int) -> int:
            new_float_value = value * (1 + factor)

            if keep_within_bounds:
                new_float_value = max(new_float_value, 0)
                new_float_value = min(new_float_value, 255)

            return int(round(new_float_value))

        return type(self)(
            lighten_channel(self.r),
            lighten_channel(self.g),
            lighten_channel(self.b),
            self.a,
        )

    def darker(self, factor: float, *, keep_within_bounds: bool = True) -> Color:
        return self.lighter(-factor, keep_within_bounds=keep_within_bounds)

    def less_transparent(self, factor: float, keep_within_bounds: bool = True) -> Color:
        new_alpha_float_value = self.a * (1 + factor)

        if keep_within_bounds:
            new_alpha_float_value = max(new_alpha_float_value, 0)
            new_alpha_float_value = min(new_alpha_float_value, 255)

        return type(self)(
            self.r,
            self.g,
            self.b,
            int(round(new_alpha_float_value)),
        )

    def more_transparent(self, factor: float, *, keep_within_bounds: bool = True) -> Color:
        return self.less_transparent(-factor, keep_within_bounds=keep_within_bounds)

    def mixed(self, other: Color) -> Color:
        return type(self)(
            int(round((self.r + other.r) / 2)),
            int(round((self.g + other.g) / 2)),
            int(round((self.b + other.b) / 2)),
            int(round((self.a + other.a) / 2)),
        )

    @property
    def compliment(self) -> Color:
        return type(self)(
            255 - self.r,
            255 - self.g,
            255 - self.b,
            self.a,
            )

    @property
    def fully_transparent(self) -> Color:
        return type(self)(
            self.r,
            self.g,
            self.b,
            0,
        )

    @property
    def fully_opaque(self) -> Color:
        return type(self)(
            self.r,
            self.g,
            self.b,
            255,
        )

    def __copy__(self) -> Color:
        return type(self)(self.r, self.g, self.b)
