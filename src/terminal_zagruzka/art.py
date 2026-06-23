"""Pixel-art banners and frame-based animations rendered with rich markup.

Everything in here is plain text + rich console markup, so it works on any
ANSI-capable terminal on Linux and macOS without external image support.
"""

from __future__ import annotations

from typing import List

# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------

# Big block "TZ" rendered with half-block characters for a chunky pixel feel.
LOGO_LINES: List[str] = [
    "████████╗ ███████╗",
    "╚══██╔══╝ ╚══███╔╝",
    "   ██║      ███╔╝ ",
    "   ██║     ███╔╝  ",
    "   ██║    ███████╗",
    "   ╚═╝    ╚══════╝",
]

# A soft cyan -> magenta gradient applied line by line to the logo.
LOGO_COLORS: List[str] = [
    "#00e5ff",
    "#28c8ff",
    "#5aa6ff",
    "#8a7dff",
    "#b85bff",
    "#e040fb",
]

TAGLINE = "terminal-zagruzka · download anything, beautifully"


def render_logo() -> str:
    """Return the logo as a rich-markup string with a vertical gradient."""
    out = []
    for line, color in zip(LOGO_LINES, LOGO_COLORS):
        out.append(f"[bold {color}]{line}[/]")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Pixel "downloading" animation
# ---------------------------------------------------------------------------

# A little pixel scene: a cloud streaming packets down into a tray.
# Each frame moves the falling pixels and pulses the colors so the terminal
# shows lively motion while a download is in progress.

_CLOUD = r"""   .--~~~~~~~~~~~~~~--.
  (   the internet     )
   `--.____________.--'"""

# The falling-packet layer. '*' marks a lit pixel position per frame.
_FALL_SLOTS = [3, 7, 11, 15, 19]


def _falling_layer(step: int) -> List[str]:
    """Three rows of packets that continuously rain downward with ``step``.

    Each column always has exactly one lit pixel, and the lit row advances
    every step, so the packets appear to fall toward the tray without gaps.
    """
    rows = [[" "] * 24 for _ in range(3)]
    for i, slot in enumerate(_FALL_SLOTS):
        # Stagger each column's phase so the rain looks organic.
        lit_row = (step + i) % 3
        rows[lit_row][slot] = "•"
    return ["".join(r) for r in rows]


_TRAY = "   ▕▏ ▁▁▁▁▁▁▁▁▁▁▁▁ ▕▏"


def download_frame(step: int) -> str:
    """Return one frame (rich markup) of the pixel download animation."""
    colors = ["#00e5ff", "#5aa6ff", "#b85bff", "#e040fb"]
    cloud_color = "#7fd1ff"
    fall = _falling_layer(step)
    lines = [f"[{cloud_color}]{line}[/]" for line in _CLOUD.splitlines()]
    for idx, row in enumerate(fall):
        c = colors[(step + idx) % len(colors)]
        lines.append(f"[bold {c}]{row}[/]")
    lines.append(f"[#8a7dff]{_TRAY}[/]")
    return "\n".join(lines)


# A compact one-line spinner made of pixel blocks for inline status.
PIXEL_SPINNER = ["▁", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃"]


def pixel_spinner(step: int, width: int = 6) -> str:
    """A scrolling block-wave spinner string of the given width."""
    frame = []
    for i in range(width):
        frame.append(PIXEL_SPINNER[(step + i) % len(PIXEL_SPINNER)])
    return "".join(frame)
