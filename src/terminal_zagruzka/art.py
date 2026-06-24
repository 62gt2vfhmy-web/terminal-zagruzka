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

# Japanese-style accents. ダウンロード = "download"; the kanji 何でも美しく
# roughly reads "everything, beautifully". A torii gate sits above the logo.
TAGLINE_JP = "ダウンロード · 何でも、美しく"
TORII = "  ⛩  ﾀｰﾐﾅﾙ・ｻﾞｸﾞﾙｽﾞｶ  ⛩"
SEIGAIHA = "🌸  ❀  ✿  ❁  ❀  ✿  ❁  ❀  🌸"


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


# ---------------------------------------------------------------------------
# Japanese-style "sakura" (cherry blossom) loading animation
# ---------------------------------------------------------------------------

# Pixel cherry-blossom petals, drifting on the wind while we work.
_PETALS = ["❀", "✿", "❁", "✾", "•", "·"]
_SAKURA_COLORS = ["#ffd1e3", "#ff9ec7", "#ff6f91", "#ff3d6e", "#ffb7d5"]

# A deterministic set of petals; each has a column, a fall phase and a wind
# drift so the field looks organic but is fully reproducible from ``step``.
_PETAL_SEEDS = [
    (2, 0, 1),
    (9, 2, 1),
    (16, 4, 2),
    (23, 1, 1),
    (30, 3, 2),
    (37, 5, 1),
    (5, 6, 2),
    (13, 1, 1),
    (20, 3, 1),
    (27, 0, 2),
    (34, 4, 1),
    (40, 2, 1),
]


def sakura_field(step: int, width: int = 44, height: int = 5) -> List[str]:
    """Return ``height`` rows (rich markup) of wind-blown cherry-blossom petals."""
    grid = [[" "] * width for _ in range(height)]
    style = [[""] * width for _ in range(height)]
    for idx, (col0, phase, drift) in enumerate(_PETAL_SEEDS):
        t = step + phase * 3
        row = t % height
        # Petals drift sideways as they fall (wind from the right).
        col = (col0 + (t // height) * drift) % width
        grid[row][col] = _PETALS[(idx + step) % len(_PETALS)]
        style[row][col] = _SAKURA_COLORS[(idx + step) % len(_SAKURA_COLORS)]

    lines = []
    for r in range(height):
        parts = []
        for c in range(width):
            ch = grid[r][c]
            if ch == " ":
                parts.append(" ")
            else:
                parts.append(f"[{style[r][c]}]{ch}[/]")
        lines.append("".join(parts))
    return lines


_LOADING_JP = ["読み込み中", "ロード中", "準備中"]


def loading_frame(step: int, message: str, width: int = 44) -> str:
    """A full sakura loading scene (rich markup) for the 'working' state."""
    petals = sakura_field(step, width=width, height=4)
    wave = pixel_spinner(step, width=10)
    jp = _LOADING_JP[(step // 6) % len(_LOADING_JP)]
    spin_color = _SAKURA_COLORS[step % len(_SAKURA_COLORS)]
    lines = list(petals)
    lines.append("")
    lines.append(
        f"[bold {spin_color}]{wave}[/]  "
        f"[bold white]{message}[/]  [italic #ff9ec7]{jp}…[/]"
    )
    return "\n".join(lines)
