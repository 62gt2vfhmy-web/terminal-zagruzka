# AGENTS.md

## Cursor Cloud specific instructions

`terminal-zagruzka` is a single-product Python CLI (commands `tz`, `utd`,
`terminal-zagruzka`): an animated `yt-dlp` front-end. There are no servers,
daemons, or databases — it runs to completion and exits. See `README.md` for
full usage and `pyproject.toml` for dependencies/scripts.

- Python dependencies are installed into a virtualenv at `.venv/` (created by the
  startup update script). Use `.venv/bin/tz` and `.venv/bin/pytest`, or activate
  with `source .venv/bin/activate`.
- `ffmpeg` and `ffprobe` are system binaries (preinstalled) and are required for
  the `mp3`/`m4a` audio presets and for merging video+audio in the `best`/`1080`/
  `720`/`480` presets.
- No linter/formatter is configured in this repo (no ruff/flake8/black/CI), so
  there is no lint step to run.
- Tests are offline/unit-based (`yt_dlp` is imported lazily), so `pytest` needs
  no network or external services.
- Running a real download requires network access plus a URL `yt-dlp` can fetch.
  For deterministic end-to-end checks, prefer a small direct file URL, e.g.
  `https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/360/Big_Buck_Bunny_360_10s_1MB.mp4`
  (note: that clip is video-only, so audio presets will fail on it). yt-dlp does
  not accept bare local file paths; to test against a local file, serve it over
  HTTP (e.g. `python3 -m http.server`) and pass the `http://...` URL.
- For clean, non-interactive logs use `--no-animation --no-info`; omit them to
  exercise the interactive animated wizard.
