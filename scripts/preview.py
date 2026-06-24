"""Render the banner and a few animation frames to stdout for visual review.

Usage: python scripts/preview.py
"""

from __future__ import annotations

import sys

from rich.console import Console

sys.path.insert(0, "src")

from terminal_zagruzka import art, ui  # noqa: E402
from terminal_zagruzka.downloader import Progress  # noqa: E402


def main() -> None:
    console = Console(force_terminal=True, width=80)
    console.print(ui.make_banner())
    console.print()
    console.rule("[bold]sakura loading frames (Japanese style)[/]")
    for step in (0, 1, 2, 3):
        console.print(f"frame {step}:")
        console.print(art.loading_frame(step, "Reading the link"), highlight=False)
        console.print()
    console.rule("[bold]pixel download frames[/]")
    for step in (0, 1, 2, 3):
        console.print(f"frame {step}:")
        console.print(art.download_frame(step), highlight=False)
        console.print()
    console.rule("[bold]live download panel mock[/]")
    p = Progress(
        status="downloading",
        filename="Never Gonna Give You Up [dQw4w9WgXcQ].mp4",
        downloaded_bytes=7_340_032,
        total_bytes=15_728_640,
        speed=2_411_724,
        eta=4,
    )
    from terminal_zagruzka.ui import _render_download_frame

    console.print(_render_download_frame(5, p, "Best quality", 0, 3))


if __name__ == "__main__":
    main()
