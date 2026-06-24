"""Thin, well-documented wrapper around yt-dlp.

This module isolates every yt-dlp detail (format strings, post-processors,
progress hooks) so the UI layer stays clean and the logic stays testable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Quality / format presets
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Preset:
    """A user-facing download preset that maps to yt-dlp options."""

    key: str
    label: str
    description: str
    # Either a format selector string, or None for "audio extraction" presets.
    format: Optional[str] = None
    # If set, audio is extracted/converted to this codec (mp3, m4a, ...).
    audio_codec: Optional[str] = None
    # Container to remux/merge video into.
    merge_container: Optional[str] = None


PRESETS: List[Preset] = [
    Preset(
        key="best",
        label="Best quality (video + audio)",
        description="Highest resolution video merged with the best audio.",
        format="bestvideo*+bestaudio/best",
        merge_container="mp4",
    ),
    Preset(
        key="1080",
        label="1080p video",
        description="Up to 1080p, merged with best audio.",
        format="bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        merge_container="mp4",
    ),
    Preset(
        key="720",
        label="720p video",
        description="Up to 720p, smaller files, great for most screens.",
        format="bestvideo[height<=720]+bestaudio/best[height<=720]",
        merge_container="mp4",
    ),
    Preset(
        key="480",
        label="480p video",
        description="Up to 480p, light and fast to download.",
        format="bestvideo[height<=480]+bestaudio/best[height<=480]",
        merge_container="mp4",
    ),
    Preset(
        key="mp3",
        label="MP3 audio only",
        description="Extract audio and convert to MP3 (needs ffmpeg).",
        audio_codec="mp3",
    ),
    Preset(
        key="m4a",
        label="M4A audio only",
        description="Extract best audio as M4A (needs ffmpeg).",
        audio_codec="m4a",
    ),
]

PRESET_BY_KEY: Dict[str, Preset] = {p.key: p for p in PRESETS}


# ---------------------------------------------------------------------------
# Progress reporting
# ---------------------------------------------------------------------------


@dataclass
class Progress:
    """Normalized snapshot of yt-dlp progress passed to the UI."""

    status: str = "idle"  # downloading | finished | error
    filename: str = ""
    downloaded_bytes: int = 0
    total_bytes: Optional[int] = None
    speed: Optional[float] = None  # bytes/sec
    eta: Optional[int] = None  # seconds
    fragment_index: Optional[int] = None
    fragment_count: Optional[int] = None

    @property
    def fraction(self) -> Optional[float]:
        if self.total_bytes and self.total_bytes > 0:
            return min(1.0, self.downloaded_bytes / self.total_bytes)
        return None


ProgressCallback = Callable[[Progress], None]


@dataclass
class DownloadConfig:
    """Everything needed to perform a download."""

    url: str
    preset: Preset
    output_dir: str = "."
    # yt-dlp template (without the directory part).
    output_template: str = "%(title)s [%(id)s].%(ext)s"
    # Restrict playlist items, e.g. "1-3,7" — None means all.
    playlist_items: Optional[str] = None
    embed_metadata: bool = True
    embed_thumbnail: bool = False
    write_subtitles: bool = False
    quiet: bool = True
    extra_opts: Dict[str, Any] = field(default_factory=dict)


def build_ydl_opts(
    config: DownloadConfig,
    progress_hook: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Translate a :class:`DownloadConfig` into a yt-dlp options dict."""
    outtmpl = os.path.join(config.output_dir, config.output_template)

    opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "noplaylist": False,
        "quiet": config.quiet,
        "no_warnings": config.quiet,
        "ignoreerrors": "only_download",
        "noprogress": True,  # we render our own progress UI
        "consoletitle": False,
        "postprocessors": [],
    }

    if progress_hook is not None:
        opts["progress_hooks"] = [progress_hook]

    if config.playlist_items:
        opts["playlist_items"] = config.playlist_items

    preset = config.preset
    if preset.audio_codec:
        # Audio-only extraction.
        opts["format"] = "bestaudio/best"
        opts["postprocessors"].append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": preset.audio_codec,
                "preferredquality": "0",  # best VBR
            }
        )
    else:
        opts["format"] = preset.format
        if preset.merge_container:
            opts["merge_output_format"] = preset.merge_container

    if config.embed_metadata:
        opts["postprocessors"].append(
            {"key": "FFmpegMetadata", "add_metadata": True}
        )

    if config.embed_thumbnail:
        opts["writethumbnail"] = True
        opts["postprocessors"].append({"key": "EmbedThumbnail"})

    if config.write_subtitles:
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = True
        opts["subtitleslangs"] = ["en.*", "en"]

    opts.update(config.extra_opts)
    return opts


def _hook_to_progress(d: Dict[str, Any]) -> Progress:
    """Convert a raw yt-dlp progress hook dict into a :class:`Progress`."""
    status = d.get("status", "idle")
    total = d.get("total_bytes") or d.get("total_bytes_estimate")
    return Progress(
        status=status,
        filename=os.path.basename(d.get("filename", "") or d.get("tmpfilename", "")),
        downloaded_bytes=int(d.get("downloaded_bytes", 0) or 0),
        total_bytes=int(total) if total else None,
        speed=d.get("speed"),
        eta=d.get("eta"),
        fragment_index=d.get("fragment_index"),
        fragment_count=d.get("fragment_count"),
    )


@dataclass
class MediaInfo:
    """Normalized metadata about a URL (single item or playlist)."""

    title: str
    is_playlist: bool
    entries: List[Dict[str, Any]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.entries) if self.is_playlist else 1

    @property
    def max_height(self) -> Optional[int]:
        """Highest video resolution detected for a single video (else None)."""
        if self.is_playlist or not self.entries:
            return None
        heights = [
            f.get("height")
            for f in (self.entries[0].get("formats") or [])
            if f.get("height")
        ]
        return max(heights) if heights else None

    @property
    def detected_qualities(self) -> List[int]:
        """Sorted (desc) list of distinct video heights for a single video."""
        if self.is_playlist or not self.entries:
            return []
        heights = {
            f.get("height")
            for f in (self.entries[0].get("formats") or [])
            if f.get("height")
        }
        return sorted(heights, reverse=True)


def probe(url: str, quiet: bool = True) -> MediaInfo:
    """Extract metadata for ``url`` without downloading anything."""
    import yt_dlp

    opts = {
        "quiet": quiet,
        "no_warnings": quiet,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "noprogress": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if info is None:
        raise RuntimeError(f"Could not extract any information from: {url}")

    if info.get("_type") == "playlist" or "entries" in info:
        entries = [e for e in (info.get("entries") or []) if e]
        return MediaInfo(
            title=info.get("title") or "Playlist",
            is_playlist=True,
            entries=entries,
            raw=info,
        )

    return MediaInfo(
        title=info.get("title") or info.get("id") or url,
        is_playlist=False,
        entries=[info],
        raw=info,
    )


def download(
    config: DownloadConfig,
    on_progress: Optional[ProgressCallback] = None,
) -> int:
    """Run a download. Returns the yt-dlp return code (0 == success)."""
    import yt_dlp

    def _raw_hook(d: Dict[str, Any]) -> None:
        if on_progress is not None:
            on_progress(_hook_to_progress(d))

    opts = build_ydl_opts(config, progress_hook=_raw_hook if on_progress else None)

    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.download([config.url])
