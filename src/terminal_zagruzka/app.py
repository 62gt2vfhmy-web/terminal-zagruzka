"""High-level orchestration that ties the UI to the downloader."""

from __future__ import annotations

import os
from typing import Optional

from . import ui
from .downloader import (
    DownloadConfig,
    Preset,
    PRESET_BY_KEY,
    PRESETS,
    download,
    probe,
)


def run_pipeline(
    url: str,
    preset: Preset,
    output_dir: str,
    playlist_items: Optional[str] = None,
    embed_thumbnail: bool = False,
    write_subtitles: bool = False,
    total_items: int = 1,
) -> int:
    os.makedirs(output_dir, exist_ok=True)
    config = DownloadConfig(
        url=url,
        preset=preset,
        output_dir=output_dir,
        playlist_items=playlist_items,
        embed_thumbnail=embed_thumbnail,
        write_subtitles=write_subtitles,
    )

    runner = ui.DownloadRunner(title=preset.label, total_items=total_items)

    def target(on_progress):
        return download(config, on_progress=on_progress)

    code = runner.run(target)
    if code == 0:
        ui.show_success(os.path.abspath(output_dir), total_items)
    else:
        ui.show_error("yt-dlp reported one or more failed downloads.")
    return code


def run_interactive(
    initial_url: Optional[str] = None,
    output_dir: Optional[str] = None,
    animate: bool = True,
) -> int:
    """The full guided experience."""
    ui.show_banner(animate=animate)

    url = initial_url or ui.ask_url()
    if not url:
        ui.show_error("No link provided. Nothing to do.")
        return 1

    ui.info("Fetching information…")
    try:
        media = probe(url)
    except Exception as exc:  # noqa: BLE001
        ui.show_error(f"Could not read that link:\n{exc}")
        return 1

    ui.show_media_info(media)

    playlist_items = None
    if media.is_playlist:
        playlist_items = ui.ask_playlist_items(media.count)

    preset = ui.choose_preset(PRESETS)

    out_dir = output_dir or ui.ask_output_dir(default=os.path.join(os.getcwd(), "downloads"))

    extras = {"embed_thumbnail": False, "write_subtitles": False}
    if not preset.audio_codec:
        extras["write_subtitles"] = ui.confirm("Also download subtitles?", default=False)
    else:
        extras["embed_thumbnail"] = ui.confirm("Embed cover art / thumbnail?", default=True)

    total_items = media.count
    if playlist_items:
        # Rough count from the range expression for the counter display.
        total_items = _count_range(playlist_items, media.count)

    return run_pipeline(
        url=url,
        preset=preset,
        output_dir=out_dir,
        playlist_items=playlist_items,
        embed_thumbnail=extras["embed_thumbnail"],
        write_subtitles=extras["write_subtitles"],
        total_items=total_items,
    )


def run_once(
    url: str,
    preset_key: str,
    output_dir: str,
    playlist_items: Optional[str] = None,
    embed_thumbnail: bool = False,
    write_subtitles: bool = False,
    animate: bool = True,
    show_info: bool = True,
) -> int:
    """Non-interactive single-shot download (driven by CLI flags)."""
    preset = PRESET_BY_KEY.get(preset_key)
    if preset is None:
        ui.show_error(
            f"Unknown format '{preset_key}'. Choose one of: "
            + ", ".join(PRESET_BY_KEY)
        )
        return 2

    if animate:
        ui.show_banner(animate=animate)

    total_items = 1
    if show_info:
        ui.info("Fetching information…")
        try:
            media = probe(url)
            ui.show_media_info(media)
            total_items = (
                _count_range(playlist_items, media.count)
                if playlist_items
                else media.count
            )
        except Exception as exc:  # noqa: BLE001
            ui.show_error(f"Could not read that link:\n{exc}")
            return 1

    return run_pipeline(
        url=url,
        preset=preset,
        output_dir=output_dir,
        playlist_items=playlist_items,
        embed_thumbnail=embed_thumbnail,
        write_subtitles=write_subtitles,
        total_items=total_items,
    )


def _count_range(expr: str, maximum: int) -> int:
    """Count how many items a yt-dlp range expression selects (best effort)."""
    if not expr:
        return maximum
    total = 0
    for part in expr.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                start_i = int(start) if start else 1
                end_i = int(end) if end else maximum
                total += max(0, end_i - start_i + 1)
            except ValueError:
                total += 1
        else:
            total += 1
    return total or maximum
