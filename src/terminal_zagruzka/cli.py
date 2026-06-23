"""Command-line entry point for terminal-zagruzka (``tz`` / ``utd``)."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from . import __version__
from .downloader import PRESETS


def _build_parser() -> argparse.ArgumentParser:
    preset_keys = [p.key for p in PRESETS]
    parser = argparse.ArgumentParser(
        prog="tz",
        description="terminal-zagruzka — a beautiful animated terminal downloader (yt-dlp).",
        epilog=(
            "Run with no arguments for the guided, animated experience, or pass a "
            "URL with --format for a one-shot download. Example:\n"
            "  tz 'https://youtu.be/...' -f mp3 -o ~/Music"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="Video or playlist URL. If omitted, you'll be prompted.",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        choices=preset_keys,
        help="Download preset. Choices: " + ", ".join(preset_keys),
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        default=None,
        help="Output folder (default: ./downloads).",
    )
    parser.add_argument(
        "-i",
        "--items",
        dest="items",
        default=None,
        help="Playlist items to grab, e.g. '1-5,8'. Default: all.",
    )
    parser.add_argument(
        "--thumbnail",
        action="store_true",
        help="Embed thumbnail / cover art (audio presets).",
    )
    parser.add_argument(
        "--subs",
        action="store_true",
        help="Also download subtitles (video presets).",
    )
    parser.add_argument(
        "--no-animation",
        action="store_true",
        help="Disable the intro and pixel animations.",
    )
    parser.add_argument(
        "--no-info",
        action="store_true",
        help="Skip the metadata probe before downloading.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"terminal-zagruzka {__version__}",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Import lazily so --help / --version stay instant.
    from . import app, ui

    animate = not args.no_animation

    try:
        # Non-interactive path: URL + explicit format provided.
        if args.url and args.format:
            return app.run_once(
                url=args.url,
                preset_key=args.format,
                output_dir=args.output or os.path.join(os.getcwd(), "downloads"),
                playlist_items=args.items,
                embed_thumbnail=args.thumbnail,
                write_subtitles=args.subs,
                animate=animate,
                show_info=not args.no_info,
            )

        # Otherwise fall into the guided, interactive experience.
        return app.run_interactive(
            initial_url=args.url,
            output_dir=args.output,
            animate=animate,
        )
    except KeyboardInterrupt:
        ui.console.print("\n[bold yellow]Cancelled.[/]")
        return 130


if __name__ == "__main__":
    sys.exit(main())
