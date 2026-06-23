import pytest

from terminal_zagruzka.cli import _build_parser, main


def test_parser_defaults():
    parser = _build_parser()
    args = parser.parse_args([])
    assert args.url is None
    assert args.format is None
    assert args.no_animation is False


def test_parser_full():
    parser = _build_parser()
    args = parser.parse_args(
        ["https://x/y", "-f", "mp3", "-o", "/tmp/m", "-i", "1-3", "--thumbnail"]
    )
    assert args.url == "https://x/y"
    assert args.format == "mp3"
    assert args.output == "/tmp/m"
    assert args.items == "1-3"
    assert args.thumbnail is True


def test_invalid_format_rejected():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["url", "-f", "nope"])


def test_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "terminal-zagruzka" in out
