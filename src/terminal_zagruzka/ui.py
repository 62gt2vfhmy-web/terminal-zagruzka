"""All terminal presentation: banner, prompts, tables and the live download view.

Built on `rich`, which renders beautifully on Linux and macOS terminals.
"""

from __future__ import annotations

import threading
import time
from typing import List, Optional

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from . import art
from .downloader import MediaInfo, Preset, PRESETS, Progress


console = Console()


# ---------------------------------------------------------------------------
# Humanizing helpers
# ---------------------------------------------------------------------------


def human_size(num: Optional[float]) -> str:
    if not num or num <= 0:
        return "—"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def human_speed(num: Optional[float]) -> str:
    if not num or num <= 0:
        return "—"
    return human_size(num) + "/s"


def human_eta(seconds: Optional[int]) -> str:
    if seconds is None or seconds < 0:
        return "—"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {sec:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def human_duration(seconds: Optional[float]) -> str:
    if not seconds:
        return "—"
    return human_eta(int(seconds))


# ---------------------------------------------------------------------------
# Banner / intro
# ---------------------------------------------------------------------------


def make_banner() -> Panel:
    logo = Text.from_markup(art.render_logo())
    torii = Text(art.TORII, style="bold #ff6f91")
    tagline = Text(art.TAGLINE, style="italic #8a7dff")
    tagline_jp = Text(art.TAGLINE_JP, style="italic #ff9ec7")
    body = Group(
        Align.center(torii),
        Text(""),
        Align.center(logo),
        Text(""),
        Align.center(tagline),
        Align.center(tagline_jp),
    )
    return Panel(
        body,
        border_style="#00e5ff",
        padding=(1, 4),
        title="[bold #e040fb]🌸 ★ 🌸[/]",
        subtitle="[#5aa6ff]powered by yt-dlp[/]",
    )


def show_banner(animate: bool = True) -> None:
    """Render the logo, optionally with a short pixel reveal animation."""
    if not animate or not console.is_terminal:
        console.print(make_banner())
        return

    banner = make_banner()
    with Live(banner, console=console, refresh_per_second=20, transient=False) as live:
        # A quick shimmer: redraw a few frames so the entrance feels alive.
        for step in range(14):
            wave = art.pixel_spinner(step, width=18)
            footer = Align.center(Text.from_markup(f"[#00e5ff]{wave}[/]"))
            live.update(Group(banner, footer))
            time.sleep(0.045)
        live.update(banner)


# ---------------------------------------------------------------------------
# Media info display
# ---------------------------------------------------------------------------


def show_media_info(info: MediaInfo) -> None:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="bold #5aa6ff", justify="right")
    table.add_column(style="white")

    if info.is_playlist:
        table.add_row("Type", "Playlist")
        table.add_row("Title", info.title)
        table.add_row("Items", str(info.count))
        preview = []
        for i, entry in enumerate(info.entries[:5], start=1):
            name = entry.get("title") or entry.get("id") or "?"
            preview.append(f"[#8a7dff]{i:>2}.[/] {name}")
        if info.count > 5:
            preview.append(f"[dim]… and {info.count - 5} more[/]")
        table.add_row("Preview", "\n".join(preview))
    else:
        entry = info.entries[0] if info.entries else {}
        table.add_row("Type", "Single video")
        table.add_row("Title", info.title)
        if entry.get("uploader"):
            table.add_row("Channel", str(entry.get("uploader")))
        if entry.get("duration"):
            table.add_row("Duration", human_duration(entry.get("duration")))
        if entry.get("view_count"):
            table.add_row("Views", f"{entry.get('view_count'):,}")
        qualities = info.detected_qualities
        if qualities:
            shown = ", ".join(f"{h}p" for h in qualities[:6])
            if len(qualities) > 6:
                shown += " …"
            table.add_row("Available", shown)

    console.print(
        Panel(table, title="[bold #00e5ff]Found[/]", border_style="#5aa6ff")
    )


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


def ask_url(default: Optional[str] = None) -> str:
    console.print()
    return Prompt.ask(
        "[bold #00e5ff]Paste a video or playlist link[/]",
        default=default or None,
        console=console,
    ).strip()


def _preset_cap(preset: Preset) -> Optional[int]:
    """Height cap implied by a video preset's key (e.g. 720). None otherwise."""
    if preset.audio_codec is not None:
        return None
    if preset.key.isdigit():
        return int(preset.key)
    return None


def choose_preset(
    presets: List[Preset] = PRESETS, max_height: Optional[int] = None
) -> Preset:
    table = Table(
        title="[bold #e040fb]🌸 Choose a format — just type a number 🌸[/]",
        border_style="#5aa6ff",
        header_style="bold #00e5ff",
    )
    table.add_column("#", justify="right", style="#8a7dff")
    table.add_column("Format", style="bold white")
    table.add_column("Details", style="dim")
    table.add_column("", style="bold")
    for i, preset in enumerate(presets, start=1):
        note = ""
        cap = _preset_cap(preset)
        if max_height and cap:
            if max_height >= cap:
                note = "[green]✓ available[/]"
            else:
                note = f"[yellow]↓ best is {max_height}p[/]"
        elif max_height is None and cap:
            note = ""
        elif preset.audio_codec:
            note = "[#ff9ec7]🎵 audio[/]"
        table.add_row(str(i), preset.label, preset.description, note)
    console.print(table)

    choice = IntPrompt.ask(
        "[bold #00e5ff]Select format[/]",
        choices=[str(i) for i in range(1, len(presets) + 1)],
        default=1,
        console=console,
    )
    return presets[choice - 1]


def ask_playlist_items(total: int) -> Optional[str]:
    console.print(
        f"[#5aa6ff]This playlist has [bold]{total}[/] items. "
        "Leave blank for all, or enter a range like [bold]1-5,8[/].[/]"
    )
    raw = Prompt.ask(
        "[bold #00e5ff]Items to download[/]", default="", console=console
    ).strip()
    return raw or None


def ask_output_dir(default: str) -> str:
    return Prompt.ask(
        "[bold #00e5ff]Save to folder[/]", default=default, console=console
    ).strip()


def confirm(prompt: str, default: bool = True) -> bool:
    from rich.prompt import Confirm

    return Confirm.ask(f"[bold #00e5ff]{prompt}[/]", default=default, console=console)


# ---------------------------------------------------------------------------
# Live download view
# ---------------------------------------------------------------------------


def _gradient_bar(fraction: float, width: int = 36) -> Text:
    fraction = max(0.0, min(1.0, fraction))
    filled = int(round(fraction * width))
    colors = ["#00e5ff", "#28c8ff", "#5aa6ff", "#8a7dff", "#b85bff", "#e040fb"]
    text = Text()
    for i in range(width):
        if i < filled:
            color = colors[int(i / max(1, width) * (len(colors) - 1))]
            text.append("█", style=color)
        else:
            text.append("░", style="grey30")
    return text


def _render_download_frame(
    step: int,
    progress: Progress,
    title: str,
    completed: int,
    total_items: int,
) -> Panel:
    anim = Text.from_markup(art.download_frame(step))

    frac = progress.fraction
    if frac is None and progress.status == "finished":
        frac = 1.0
    bar = _gradient_bar(frac if frac is not None else 0.0)
    pct = f"{frac * 100:5.1f}%" if frac is not None else "  ?  %"

    stats = Table.grid(padding=(0, 2))
    stats.add_column(justify="right", style="#5aa6ff")
    stats.add_column(style="white")
    stats.add_row("File", Text(progress.filename or "—", overflow="ellipsis"))
    stats.add_row(
        "Size",
        f"{human_size(progress.downloaded_bytes)} / {human_size(progress.total_bytes)}",
    )
    stats.add_row("Speed", human_speed(progress.speed))
    stats.add_row("ETA", human_eta(progress.eta))
    if total_items > 1:
        stats.add_row("Item", f"{min(completed + 1, total_items)} / {total_items}")

    wave = art.pixel_spinner(step, width=10)
    bar_line = Group(
        Text.from_markup(f"[#00e5ff]{wave}[/]  ") + bar + Text(f"  {pct}", style="bold #e040fb"),
    )

    body = Group(
        Align.center(anim),
        Text(""),
        bar_line,
        Text(""),
        stats,
    )
    return Panel(
        body,
        title=f"[bold #00e5ff]Downloading[/] [white]{title}[/]",
        border_style="#e040fb",
        padding=(1, 3),
    )


class DownloadRunner:
    """Drives a download in a background thread while animating in the foreground."""

    def __init__(self, title: str, total_items: int = 1) -> None:
        self.title = title
        self.total_items = total_items
        self._lock = threading.Lock()
        self._progress = Progress()
        self._completed_items = 0
        self._finished = False
        self._error: Optional[BaseException] = None
        self._return_code: Optional[int] = None

    # -- callbacks fed from the downloader thread -------------------------
    def on_progress(self, progress: Progress) -> None:
        with self._lock:
            if progress.status == "finished":
                self._completed_items += 1
            self._progress = progress

    def _snapshot(self):
        with self._lock:
            return self._progress, self._completed_items

    # -- the public entry point ------------------------------------------
    def run(self, target) -> int:
        """``target`` is a zero-arg callable returning the yt-dlp return code."""

        def worker() -> None:
            try:
                self._return_code = target(self.on_progress)
            except BaseException as exc:  # noqa: BLE001 - surfaced to caller
                self._error = exc
            finally:
                self._finished = True

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        if console.is_terminal:
            self._animate(thread)
        else:
            thread.join()

        if self._error is not None:
            raise self._error
        return self._return_code if self._return_code is not None else 1

    def _animate(self, thread: threading.Thread) -> None:
        step = 0
        with Live(console=console, refresh_per_second=15, transient=True) as live:
            while not self._finished:
                progress, completed = self._snapshot()
                live.update(
                    _render_download_frame(
                        step, progress, self.title, completed, self.total_items
                    )
                )
                step += 1
                time.sleep(0.066)
            thread.join()


def show_success(paths_hint: str, count: int) -> None:
    msg = Text()
    msg.append("✔ ", style="bold green")
    msg.append(f"Done! Downloaded {count} item(s).\n", style="bold white")
    msg.append("Saved to: ", style="#5aa6ff")
    msg.append(paths_hint, style="bold #00e5ff")
    console.print(Panel(msg, border_style="green", title="[bold green]Complete[/]"))


def show_error(message: str) -> None:
    console.print(
        Panel(
            Text(message, style="bold white"),
            border_style="red",
            title="[bold red]Error[/]",
        )
    )


def info(message: str) -> None:
    console.print(f"[#5aa6ff]›[/] {message}")


def run_with_loader(message: str, target):
    """Run ``target()`` in a background thread while animating sakura petals.

    Returns whatever ``target`` returns; re-raises any exception it throws.
    Falls back to a plain status line when stdout is not a terminal.
    """
    result: dict = {}
    box: dict = {}

    def worker() -> None:
        try:
            result["value"] = target()
        except BaseException as exc:  # noqa: BLE001 - surfaced to caller
            box["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    if console.is_terminal:
        step = 0
        with Live(console=console, refresh_per_second=15, transient=True) as live:
            while thread.is_alive():
                frame = Text.from_markup(art.loading_frame(step, message))
                live.update(
                    Panel(
                        Align.center(frame),
                        border_style="#ff6f91",
                        title="[bold #ff9ec7]🌸 ロード中 🌸[/]",
                        padding=(1, 3),
                    )
                )
                step += 1
                time.sleep(0.066)
        thread.join()
    else:
        info(message)
        thread.join()

    if "error" in box:
        raise box["error"]
    return result.get("value")
