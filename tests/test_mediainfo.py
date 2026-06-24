from terminal_zagruzka.downloader import MediaInfo


def _single_with_formats(heights):
    formats = [{"height": h} for h in heights] + [{"height": None}]
    return MediaInfo(
        title="x",
        is_playlist=False,
        entries=[{"title": "x", "formats": formats}],
    )


def test_max_height_single():
    info = _single_with_formats([360, 720, 1080])
    assert info.max_height == 1080


def test_detected_qualities_sorted_desc_unique():
    info = _single_with_formats([360, 720, 720, 1080])
    assert info.detected_qualities == [1080, 720, 360]


def test_playlist_has_no_heights():
    info = MediaInfo(title="pl", is_playlist=True, entries=[{"id": "a"}, {"id": "b"}])
    assert info.max_height is None
    assert info.detected_qualities == []
    assert info.count == 2


def test_single_without_formats():
    info = MediaInfo(title="x", is_playlist=False, entries=[{"title": "x"}])
    assert info.max_height is None
    assert info.detected_qualities == []
