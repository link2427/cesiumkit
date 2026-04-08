"""Color system for cesiumkit, matching all CesiumJS named colors."""

from __future__ import annotations

import random

from pydantic import PrivateAttr

from cesiumkit.base import CesiumBase


class Color(CesiumBase):
    """Represents a Cesium color with RGBA components (0.0 to 1.0)."""

    red: float = 1.0
    green: float = 1.0
    blue: float = 1.0
    alpha: float = 1.0
    _named: str | None = PrivateAttr(default=None)

    def _js_class_name(self) -> str:
        return "Cesium.Color"

    def to_js(self) -> str:
        if self._named:
            # Check if this is a named color used at its original alpha
            orig = _NAMED_COLORS_ALPHA.get(self._named, 1.0)
            if self.alpha != orig:
                return f"Cesium.Color.{self._named}.withAlpha({self.alpha})"
            return f"Cesium.Color.{self._named}"
        return f"new Cesium.Color({self.red}, {self.green}, {self.blue}, {self.alpha})"

    def to_czml(self) -> dict:
        return {
            "rgba": [
                int(self.red * 255),
                int(self.green * 255),
                int(self.blue * 255),
                int(self.alpha * 255),
            ]
        }

    def with_alpha(self, alpha: float) -> Color:
        """Return a new Color with the given alpha value."""
        c = Color(red=self.red, green=self.green, blue=self.blue, alpha=alpha)
        c._named = self._named
        return c

    @classmethod
    def from_bytes(cls, red: int, green: int, blue: int, alpha: int = 255) -> Color:
        """Create a Color from byte values (0-255)."""
        return cls(
            red=red / 255.0,
            green=green / 255.0,
            blue=blue / 255.0,
            alpha=alpha / 255.0,
        )

    @classmethod
    def from_css(cls, css_string: str) -> Color:
        """Create a Color from a CSS color string.

        Supports #RRGGBB and #RRGGBBAA hex formats.
        """
        s = css_string.lstrip("#")
        if len(s) == 6:
            r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
            return cls.from_bytes(r, g, b)
        elif len(s) == 8:
            r, g, b, a = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), int(s[6:8], 16)
            return cls.from_bytes(r, g, b, a)
        raise ValueError(f"Unsupported CSS color format: {css_string}")

    @classmethod
    def from_random(
        cls,
        red: float | None = None,
        green: float | None = None,
        blue: float | None = None,
        alpha: float | None = None,
    ) -> Color:
        """Create a Color with random components. Fixed values can be provided."""
        return cls(
            red=red if red is not None else random.random(),
            green=green if green is not None else random.random(),
            blue=blue if blue is not None else random.random(),
            alpha=alpha if alpha is not None else 1.0,
        )


def _named_color(name: str, r: float, g: float, b: float, a: float = 1.0) -> Color:
    """Create a named color constant."""
    c = Color(red=r, green=g, blue=b, alpha=a)
    c._named = name
    return c


# Map of named colors to their original alpha value (most are 1.0)
_NAMED_COLORS_ALPHA: dict[str, float] = {"TRANSPARENT": 0.0}

# All 148 CesiumJS named color constants
ALICEBLUE = _named_color("ALICEBLUE", 0.941176, 0.972549, 1.0)
ANTIQUEWHITE = _named_color("ANTIQUEWHITE", 0.980392, 0.921569, 0.843137)
AQUA = _named_color("AQUA", 0.0, 1.0, 1.0)
AQUAMARINE = _named_color("AQUAMARINE", 0.498039, 1.0, 0.831373)
AZURE = _named_color("AZURE", 0.941176, 1.0, 1.0)
BEIGE = _named_color("BEIGE", 0.960784, 0.960784, 0.862745)
BISQUE = _named_color("BISQUE", 1.0, 0.894118, 0.768627)
BLACK = _named_color("BLACK", 0.0, 0.0, 0.0)
BLANCHEDALMOND = _named_color("BLANCHEDALMOND", 1.0, 0.921569, 0.803922)
BLUE = _named_color("BLUE", 0.0, 0.0, 1.0)
BLUEVIOLET = _named_color("BLUEVIOLET", 0.541176, 0.168627, 0.886275)
BROWN = _named_color("BROWN", 0.647059, 0.164706, 0.164706)
BURLYWOOD = _named_color("BURLYWOOD", 0.870588, 0.721569, 0.529412)
CADETBLUE = _named_color("CADETBLUE", 0.372549, 0.619608, 0.627451)
CHARTREUSE = _named_color("CHARTREUSE", 0.498039, 1.0, 0.0)
CHOCOLATE = _named_color("CHOCOLATE", 0.823529, 0.411765, 0.117647)
CORAL = _named_color("CORAL", 1.0, 0.498039, 0.313725)
CORNFLOWERBLUE = _named_color("CORNFLOWERBLUE", 0.392157, 0.584314, 0.929412)
CORNSILK = _named_color("CORNSILK", 1.0, 0.972549, 0.862745)
CRIMSON = _named_color("CRIMSON", 0.862745, 0.078431, 0.235294)
CYAN = _named_color("CYAN", 0.0, 1.0, 1.0)
DARKBLUE = _named_color("DARKBLUE", 0.0, 0.0, 0.545098)
DARKCYAN = _named_color("DARKCYAN", 0.0, 0.545098, 0.545098)
DARKGOLDENROD = _named_color("DARKGOLDENROD", 0.721569, 0.525490, 0.043137)
DARKGRAY = _named_color("DARKGRAY", 0.662745, 0.662745, 0.662745)
DARKGREEN = _named_color("DARKGREEN", 0.0, 0.392157, 0.0)
DARKGREY = _named_color("DARKGREY", 0.662745, 0.662745, 0.662745)
DARKKHAKI = _named_color("DARKKHAKI", 0.741176, 0.717647, 0.419608)
DARKMAGENTA = _named_color("DARKMAGENTA", 0.545098, 0.0, 0.545098)
DARKOLIVEGREEN = _named_color("DARKOLIVEGREEN", 0.333333, 0.419608, 0.184314)
DARKORANGE = _named_color("DARKORANGE", 1.0, 0.549020, 0.0)
DARKORCHID = _named_color("DARKORCHID", 0.6, 0.196078, 0.8)
DARKRED = _named_color("DARKRED", 0.545098, 0.0, 0.0)
DARKSALMON = _named_color("DARKSALMON", 0.913725, 0.588235, 0.478431)
DARKSEAGREEN = _named_color("DARKSEAGREEN", 0.560784, 0.737255, 0.560784)
DARKSLATEBLUE = _named_color("DARKSLATEBLUE", 0.282353, 0.239216, 0.545098)
DARKSLATEGRAY = _named_color("DARKSLATEGRAY", 0.184314, 0.309804, 0.309804)
DARKSLATEGREY = _named_color("DARKSLATEGREY", 0.184314, 0.309804, 0.309804)
DARKTURQUOISE = _named_color("DARKTURQUOISE", 0.0, 0.807843, 0.819608)
DARKVIOLET = _named_color("DARKVIOLET", 0.580392, 0.0, 0.827451)
DEEPPINK = _named_color("DEEPPINK", 1.0, 0.078431, 0.576471)
DEEPSKYBLUE = _named_color("DEEPSKYBLUE", 0.0, 0.749020, 1.0)
DIMGRAY = _named_color("DIMGRAY", 0.411765, 0.411765, 0.411765)
DIMGREY = _named_color("DIMGREY", 0.411765, 0.411765, 0.411765)
DODGERBLUE = _named_color("DODGERBLUE", 0.117647, 0.564706, 1.0)
FIREBRICK = _named_color("FIREBRICK", 0.698039, 0.133333, 0.133333)
FLORALWHITE = _named_color("FLORALWHITE", 1.0, 0.980392, 0.941176)
FORESTGREEN = _named_color("FORESTGREEN", 0.133333, 0.545098, 0.133333)
FUCHSIA = _named_color("FUCHSIA", 1.0, 0.0, 1.0)
GAINSBORO = _named_color("GAINSBORO", 0.862745, 0.862745, 0.862745)
GHOSTWHITE = _named_color("GHOSTWHITE", 0.972549, 0.972549, 1.0)
GOLD = _named_color("GOLD", 1.0, 0.843137, 0.0)
GOLDENROD = _named_color("GOLDENROD", 0.854902, 0.647059, 0.125490)
GRAY = _named_color("GRAY", 0.501961, 0.501961, 0.501961)
GREEN = _named_color("GREEN", 0.0, 0.501961, 0.0)
GREENYELLOW = _named_color("GREENYELLOW", 0.678431, 1.0, 0.184314)
GREY = _named_color("GREY", 0.501961, 0.501961, 0.501961)
HONEYDEW = _named_color("HONEYDEW", 0.941176, 1.0, 0.941176)
HOTPINK = _named_color("HOTPINK", 1.0, 0.411765, 0.705882)
INDIANRED = _named_color("INDIANRED", 0.803922, 0.360784, 0.360784)
INDIGO = _named_color("INDIGO", 0.294118, 0.0, 0.509804)
IVORY = _named_color("IVORY", 1.0, 1.0, 0.941176)
KHAKI = _named_color("KHAKI", 0.941176, 0.901961, 0.549020)
LAVENDER = _named_color("LAVENDER", 0.901961, 0.901961, 0.980392)
LAVENDERBLUSH = _named_color("LAVENDERBLUSH", 1.0, 0.941176, 0.960784)
LAWNGREEN = _named_color("LAWNGREEN", 0.486275, 0.988235, 0.0)
LEMONCHIFFON = _named_color("LEMONCHIFFON", 1.0, 0.980392, 0.803922)
LIGHTBLUE = _named_color("LIGHTBLUE", 0.678431, 0.847059, 0.901961)
LIGHTCORAL = _named_color("LIGHTCORAL", 0.941176, 0.501961, 0.501961)
LIGHTCYAN = _named_color("LIGHTCYAN", 0.878431, 1.0, 1.0)
LIGHTGOLDENRODYELLOW = _named_color("LIGHTGOLDENRODYELLOW", 0.980392, 0.980392, 0.823529)
LIGHTGRAY = _named_color("LIGHTGRAY", 0.827451, 0.827451, 0.827451)
LIGHTGREEN = _named_color("LIGHTGREEN", 0.564706, 0.933333, 0.564706)
LIGHTGREY = _named_color("LIGHTGREY", 0.827451, 0.827451, 0.827451)
LIGHTPINK = _named_color("LIGHTPINK", 1.0, 0.713725, 0.756863)
LIGHTSALMON = _named_color("LIGHTSALMON", 1.0, 0.627451, 0.478431)
LIGHTSEAGREEN = _named_color("LIGHTSEAGREEN", 0.125490, 0.698039, 0.666667)
LIGHTSKYBLUE = _named_color("LIGHTSKYBLUE", 0.529412, 0.807843, 0.980392)
LIGHTSLATEGRAY = _named_color("LIGHTSLATEGRAY", 0.466667, 0.533333, 0.6)
LIGHTSLATEGREY = _named_color("LIGHTSLATEGREY", 0.466667, 0.533333, 0.6)
LIGHTSTEELBLUE = _named_color("LIGHTSTEELBLUE", 0.690196, 0.768627, 0.870588)
LIGHTYELLOW = _named_color("LIGHTYELLOW", 1.0, 1.0, 0.878431)
LIME = _named_color("LIME", 0.0, 1.0, 0.0)
LIMEGREEN = _named_color("LIMEGREEN", 0.196078, 0.803922, 0.196078)
LINEN = _named_color("LINEN", 0.980392, 0.941176, 0.901961)
MAGENTA = _named_color("MAGENTA", 1.0, 0.0, 1.0)
MAROON = _named_color("MAROON", 0.501961, 0.0, 0.0)
MEDIUMAQUAMARINE = _named_color("MEDIUMAQUAMARINE", 0.4, 0.803922, 0.666667)
MEDIUMBLUE = _named_color("MEDIUMBLUE", 0.0, 0.0, 0.803922)
MEDIUMORCHID = _named_color("MEDIUMORCHID", 0.729412, 0.333333, 0.827451)
MEDIUMPURPLE = _named_color("MEDIUMPURPLE", 0.576471, 0.439216, 0.858824)
MEDIUMSEAGREEN = _named_color("MEDIUMSEAGREEN", 0.235294, 0.701961, 0.443137)
MEDIUMSLATEBLUE = _named_color("MEDIUMSLATEBLUE", 0.482353, 0.407843, 0.933333)
MEDIUMSPRINGGREEN = _named_color("MEDIUMSPRINGGREEN", 0.0, 0.980392, 0.603922)
MEDIUMTURQUOISE = _named_color("MEDIUMTURQUOISE", 0.282353, 0.819608, 0.8)
MEDIUMVIOLETRED = _named_color("MEDIUMVIOLETRED", 0.780392, 0.082353, 0.521569)
MIDNIGHTBLUE = _named_color("MIDNIGHTBLUE", 0.098039, 0.098039, 0.439216)
MINTCREAM = _named_color("MINTCREAM", 0.960784, 1.0, 0.980392)
MISTYROSE = _named_color("MISTYROSE", 1.0, 0.894118, 0.882353)
MOCCASIN = _named_color("MOCCASIN", 1.0, 0.894118, 0.709804)
NAVAJOWHITE = _named_color("NAVAJOWHITE", 1.0, 0.870588, 0.678431)
NAVY = _named_color("NAVY", 0.0, 0.0, 0.501961)
OLDLACE = _named_color("OLDLACE", 0.992157, 0.960784, 0.901961)
OLIVE = _named_color("OLIVE", 0.501961, 0.501961, 0.0)
OLIVEDRAB = _named_color("OLIVEDRAB", 0.419608, 0.556863, 0.137255)
ORANGE = _named_color("ORANGE", 1.0, 0.647059, 0.0)
ORANGERED = _named_color("ORANGERED", 1.0, 0.270588, 0.0)
ORCHID = _named_color("ORCHID", 0.854902, 0.439216, 0.839216)
PALEGOLDENROD = _named_color("PALEGOLDENROD", 0.933333, 0.909804, 0.666667)
PALEGREEN = _named_color("PALEGREEN", 0.596078, 0.984314, 0.596078)
PALETURQUOISE = _named_color("PALETURQUOISE", 0.686275, 0.933333, 0.933333)
PALEVIOLETRED = _named_color("PALEVIOLETRED", 0.858824, 0.439216, 0.576471)
PAPAYAWHIP = _named_color("PAPAYAWHIP", 1.0, 0.937255, 0.835294)
PEACHPUFF = _named_color("PEACHPUFF", 1.0, 0.854902, 0.725490)
PERU = _named_color("PERU", 0.803922, 0.521569, 0.247059)
PINK = _named_color("PINK", 1.0, 0.752941, 0.796078)
PLUM = _named_color("PLUM", 0.866667, 0.627451, 0.866667)
POWDERBLUE = _named_color("POWDERBLUE", 0.690196, 0.878431, 0.901961)
PURPLE = _named_color("PURPLE", 0.501961, 0.0, 0.501961)
RED = _named_color("RED", 1.0, 0.0, 0.0)
ROSYBROWN = _named_color("ROSYBROWN", 0.737255, 0.560784, 0.560784)
ROYALBLUE = _named_color("ROYALBLUE", 0.254902, 0.411765, 0.882353)
SADDLEBROWN = _named_color("SADDLEBROWN", 0.545098, 0.270588, 0.074510)
SALMON = _named_color("SALMON", 0.980392, 0.501961, 0.447059)
SANDYBROWN = _named_color("SANDYBROWN", 0.956863, 0.643137, 0.376471)
SEAGREEN = _named_color("SEAGREEN", 0.180392, 0.545098, 0.341176)
SEASHELL = _named_color("SEASHELL", 1.0, 0.960784, 0.933333)
SIENNA = _named_color("SIENNA", 0.627451, 0.321569, 0.176471)
SILVER = _named_color("SILVER", 0.752941, 0.752941, 0.752941)
SKYBLUE = _named_color("SKYBLUE", 0.529412, 0.807843, 0.921569)
SLATEBLUE = _named_color("SLATEBLUE", 0.415686, 0.352941, 0.803922)
SLATEGRAY = _named_color("SLATEGRAY", 0.439216, 0.501961, 0.564706)
SLATEGREY = _named_color("SLATEGREY", 0.439216, 0.501961, 0.564706)
SNOW = _named_color("SNOW", 1.0, 0.980392, 0.980392)
SPRINGGREEN = _named_color("SPRINGGREEN", 0.0, 1.0, 0.498039)
STEELBLUE = _named_color("STEELBLUE", 0.274510, 0.509804, 0.705882)
TAN = _named_color("TAN", 0.823529, 0.705882, 0.549020)
TEAL = _named_color("TEAL", 0.0, 0.501961, 0.501961)
THISTLE = _named_color("THISTLE", 0.847059, 0.749020, 0.847059)
TOMATO = _named_color("TOMATO", 1.0, 0.388235, 0.278431)
TRANSPARENT = _named_color("TRANSPARENT", 0.0, 0.0, 0.0, 0.0)
TURQUOISE = _named_color("TURQUOISE", 0.250980, 0.878431, 0.815686)
VIOLET = _named_color("VIOLET", 0.933333, 0.509804, 0.933333)
WHEAT = _named_color("WHEAT", 0.960784, 0.870588, 0.701961)
WHITE = _named_color("WHITE", 1.0, 1.0, 1.0)
WHITESMOKE = _named_color("WHITESMOKE", 0.960784, 0.960784, 0.960784)
YELLOW = _named_color("YELLOW", 1.0, 1.0, 0.0)
YELLOWGREEN = _named_color("YELLOWGREEN", 0.603922, 0.803922, 0.196078)
