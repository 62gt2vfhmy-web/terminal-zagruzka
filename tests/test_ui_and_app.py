from terminal_zagruzka import art, ui
from terminal_zagruzka.app import _count_range


def test_human_size():
    assert ui.human_size(0) == "—"
    assert ui.human_size(512) == "512 B"
    assert ui.human_size(1536).endswith("KB")
    assert ui.human_size(5 * 1024 * 1024).endswith("MB")


def test_human_speed():
    assert ui.human_speed(None) == "—"
    assert ui.human_speed(1024).endswith("/s")


def test_human_eta():
    assert ui.human_eta(None) == "—"
    assert ui.human_eta(5) == "5s"
    assert ui.human_eta(90) == "1m 30s"
    assert ui.human_eta(3700) == "1h 01m"


def test_gradient_bar_width():
    bar = ui._gradient_bar(0.5, width=20)
    assert len(bar.plain) == 20


def test_gradient_bar_clamped():
    assert len(ui._gradient_bar(2.0, width=10).plain) == 10
    assert len(ui._gradient_bar(-1.0, width=10).plain) == 10


def test_art_logo_lines_aligned():
    assert len(art.LOGO_LINES) == len(art.LOGO_COLORS)


def test_download_frame_is_string():
    frame = art.download_frame(0)
    assert isinstance(frame, str)
    assert "the internet" in frame


def test_falling_layer_always_has_motion():
    # Every step should light up packets (no fully empty frames).
    for step in range(6):
        rows = art._falling_layer(step)
        assert any("•" in r for r in rows)


def test_pixel_spinner_length():
    assert len(art.pixel_spinner(0, width=8)) == 8


def test_count_range():
    assert _count_range("", 10) == 10
    assert _count_range("1-5", 10) == 5
    assert _count_range("1-3,7", 10) == 4
    assert _count_range("2-", 10) == 9
    assert _count_range("-3", 10) == 3
