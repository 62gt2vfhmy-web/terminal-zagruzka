import os

import pytest

from terminal_zagruzka.downloader import (
    DownloadConfig,
    PRESET_BY_KEY,
    Progress,
    _hook_to_progress,
    build_ydl_opts,
)


def _cfg(preset_key, **kw):
    return DownloadConfig(url="http://example/x", preset=PRESET_BY_KEY[preset_key], **kw)


def test_video_preset_sets_format_and_merge():
    opts = build_ydl_opts(_cfg("720", output_dir="/tmp/out"))
    assert opts["format"].startswith("bestvideo[height<=720]")
    assert opts["merge_output_format"] == "mp4"
    assert opts["outtmpl"].startswith(os.path.join("/tmp/out", ""))


def test_best_preset():
    opts = build_ydl_opts(_cfg("best"))
    assert opts["format"] == "bestvideo*+bestaudio/best"
    assert opts["merge_output_format"] == "mp4"


def test_mp3_preset_adds_extract_audio_postprocessor():
    opts = build_ydl_opts(_cfg("mp3"))
    assert opts["format"] == "bestaudio/best"
    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "FFmpegExtractAudio" in keys
    codec = next(pp for pp in opts["postprocessors"] if pp["key"] == "FFmpegExtractAudio")
    assert codec["preferredcodec"] == "mp3"


def test_playlist_items_passthrough():
    opts = build_ydl_opts(_cfg("best", playlist_items="1-3,7"))
    assert opts["playlist_items"] == "1-3,7"


def test_subtitles_option():
    opts = build_ydl_opts(_cfg("best", write_subtitles=True))
    assert opts["writesubtitles"] is True
    assert opts["writeautomaticsub"] is True


def test_thumbnail_option():
    opts = build_ydl_opts(_cfg("mp3", embed_thumbnail=True))
    assert opts["writethumbnail"] is True
    assert any(pp["key"] == "EmbedThumbnail" for pp in opts["postprocessors"])


def test_progress_hook_conversion_and_fraction():
    p = _hook_to_progress(
        {
            "status": "downloading",
            "filename": "/a/b/video.mp4",
            "downloaded_bytes": 50,
            "total_bytes": 200,
            "speed": 1000.0,
            "eta": 3,
        }
    )
    assert p.status == "downloading"
    assert p.filename == "video.mp4"
    assert p.fraction == pytest.approx(0.25)


def test_progress_fraction_none_without_total():
    assert Progress(downloaded_bytes=10).fraction is None


def test_progress_hook_estimate_total():
    p = _hook_to_progress(
        {"status": "downloading", "downloaded_bytes": 10, "total_bytes_estimate": 100}
    )
    assert p.total_bytes == 100
