# History

## 0.3.0.b2 (2025-08-31)

- Add HTTP JSON endpoint `GET /now_playing?channel=<id|name|number>` to return current track info
- Add CLI `--quiet`/`-Q` flag (ERROR logging); default logging is WARNING; `--verbose` sets DEBUG
- Refresh README with quick start and endpoint docs

## 0.3.0.b1

Everything from here on is my personal additoins to the codebase and
highly opinionated to use astral.sh tools: uv, ruff, ty etc.

## 0.2.8 (2021-07-24)

- Precache m3u8 playlists

## 0.2.7 (2021-07-23)

- Adds caching of HLS chunks to HLS proxy to make it more resilient to
  network issues
- HLS chunk caching can be disabled with [-n]{.title-ref} or
  [\--no-precache]{.title-ref}
- Speeds up [XMLiveChannel.get_latest_cut]{.title-ref}

## 0.2.6 (2021-07-17)

- Fixes secondary HLS URL generation

## 0.2.5 (2021-07-16)

- Pulls [tune_time]{.title-ref} from [wallClockRenderTime]{.title-ref}
- Adds [primary_hls]{.title-ref} and [seconary_hls]{.title-ref}
- Adds quality selection
- Overhauls time/datetime management
- Adds automatic failover to secondary HLS

## 0.2.4 (2021-07-15)

- Fixes pydantic issue in [XMLiveChannel]{.title-ref}
- Adjusts selected HLS stream to (hopefully) fix
  [radio_time]{.title-ref}
- Switches HTTP server to using [aiohttp]{.title-ref}
- Adds [SXMClientAsync]{.title-ref}

## 0.2.3 (2021-07-15)

- Splits typer params out into seperate variables

## 0.2.2 (2021-07-15)

- Adds type stubs

## 0.2.0 (2021-07-15)

- Fixes authentication (thanks \@Lustyn)
- Replaces setuptools with filt
- Replaces click with typer
- Replaces requests with httpx
- Updates linting
- Replaces TravisCI with Github Actions
- Adds Pydantic for SXM models

## 0.1.0 (2018-12-25)

- First release on PyPI.
