# sxm-client

## Warning

Designed for PERSONAL USE ONLY

`sxm` is a 100% unofficial project and you use it at your own risk. It is designed to be used for personal use with a small number of users listening to it at once. Similar to playing music over a speak from the radio directly. Using `sxm-player` in any corporate setting, to attempt to pirate music, or to try to make a profit off your subscription may result in you getting in legal trouble.

### About

`sxm-client` is a Python library and small HTTP proxy designed to help write
applications for the SiriusXM (XM Radio) service.

- Free software: MIT license
- Documentation: <http://sxm-client.readthedocs.io/>.

## Features

- A simple HTTP proxy server that can serve HLS streams for SXM channels
- Python SXM client (sync + async)
- Python classes to interface with SXM channel data
- JSON API endpoint for current track: `GET /now_playing?channel=<id|name|number>`

For details on usage and installation, see the [documentation](http://sxm-client.readthedocs.io/).

## Quick start

1. Install (uv recommended):

```bash
uv pip install -e .
```

1. Run the proxy server:

```bash
sxm server -U "$SXM_USERNAME" -P "$SXM_PASSWORD" --host 127.0.0.1 --port 9999
```

1. Fetch currently playing track as JSON:

```bash
curl 'http://127.0.0.1:9999/now_playing?channel=octane'
```

Response example:

```json
{
  "channel_id": "octane",
  "title": "The Pretender",
  "artist": "Foo Fighters",
  "album": "Echoes, Silence, Patience & Grace",
  "played_at_ms": 1725110473123
}
```

## CLI flags of interest

- `-v`, `--verbose`: enable DEBUG logging
- `-Q`, `--quiet`: reduce logging to ERROR only
- default logging level: WARNING

`sxm-client` is designed to be a bare bones library to setup an anonymous HLS stream. For a more in-depth applications, check out [sxm-player](https://github.com/AngellusMortis/sxm-player).

## Credits

Huge props to andrew0 <andrew0@github.com> for for reverse engineering the original SXM APIs used

Huge props to <https://github.com/AngellusMortis/sxm-client> for the version this is based on.
