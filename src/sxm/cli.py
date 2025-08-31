# -*- coding: utf-8 -*-

"""Console script for sxm."""

import logging

import typer

from sxm import QualitySize, RegionChoice, SXMClient, run_http_server

app = typer.Typer()


OPTION_USERNAME = typer.Option(
    ...,
    "--username",
    "-U",
    help="SXM username",
    prompt=True,
    envvar="SXM_USERNAME",
)
OPTION_PASSWORD = typer.Option(
    ...,
    "--password",
    "-P",
    help="SXM password",
    prompt=True,
    hide_input=True,
    envvar="SXM_PASSWORD",
)
OPTION_PORT = typer.Option(
    9999, "--port", "-p", help="Port to run SXM server on", envvar="SXM_PORT"
)
OPTION_HOST = typer.Option(
    "127.0.0.1", "--host", "-h", help="IP to bind SXM server to", envvar="SXM_HOST"
)
OPTION_VERBOSE = typer.Option(
    False, "--verbose", "-v", help="Enable debug logging", envvar="SXM_DEBUG"
)
OPTION_QUIET = typer.Option(
    False, "--quiet", "-Q", help="Reduce logging verbosity (ERROR level)", envvar="SXM_QUIET"
)
OPTION_REGION = typer.Option(
    RegionChoice.US,
    "--region",
    "-r",
    help="Sets the SXM client's region",
    envvar="SXM_REGION",
)
OPTION_QUALITY = typer.Option(
    QualitySize.LARGE_256k,
    "--quality",
    "-q",
    help="Sets stream qualuty.",
    envvar="SXM_REGION",
)
OPTION_PRECACHE = typer.Option(
    True,
    "--no-precache",
    "-n",
    help="Turn off precaching AAC chunks",
    envvar="SXM_PRECACHE",
)


@app.command()
def server(
    username: str = OPTION_USERNAME,
    password: str = OPTION_PASSWORD,
    port: int = OPTION_PORT,
    host: str = OPTION_HOST,
    verbose: bool = OPTION_VERBOSE,
    quiet: bool = OPTION_QUIET,
    region: RegionChoice = OPTION_REGION,
    quality: QualitySize = OPTION_QUALITY,
    precache: bool = OPTION_PRECACHE,
) -> int:
    """SXM proxy command line application."""

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)

    with SXMClient(username, password, region=region, quality=quality) as sxm:
        run_http_server(sxm, port, ip=host, precache=precache)
    return 0


@app.command()
def list_channels(
    username: str = OPTION_USERNAME,
    password: str = OPTION_PASSWORD,
    verbose: bool = OPTION_VERBOSE,
    quiet: bool = OPTION_QUIET,
    region: RegionChoice = OPTION_REGION,
    quality: QualitySize = OPTION_QUALITY,
) -> int:
    """Lists all available channels."""

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)

    with SXMClient(username, password, region=region, quality=quality) as sxm:
        channels = sxm.channels
        l1 = max(len(x.id) for x in channels)
        l2 = max(len(str(x.channel_number)) for x in channels)
        l3 = max(len(x.name) for x in channels)

        typer.echo(f"{'ID'.ljust(l1)} | {'Num'.ljust(l2)} | {'Name'.ljust(l3)}")
        for channel in channels:
            channel_id = channel.id.ljust(l1)[:l1]
            channel_num = str(channel.channel_number).ljust(l2)[:l2]
            channel_name = channel.name.ljust(l3)[:l3]
            typer.echo(f"{channel_id} | {channel_num} | {channel_name}")
    return 0


@app.command()
def now_playing(
    channel_id: str = typer.Argument(..., help="Channel ID to check"),
    username: str = OPTION_USERNAME,
    password: str = OPTION_PASSWORD,
    verbose: bool = OPTION_VERBOSE,
    quiet: bool = OPTION_QUIET,
    region: RegionChoice = OPTION_REGION,
    quality: QualitySize = OPTION_QUALITY,
) -> int:
    """Gets the currently playing song on a channel."""

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)

    with SXMClient(username, password, region=region, quality=quality) as sxm:
        # Resolve provided identifier to a channel object first
        channel = sxm.get_channel(channel_id)
        if channel is None:
            typer.echo(f"No channel found for '{channel_id}'")
            return 1

        data = sxm.get_now_playing(channel)
        if data is None:
            typer.echo(f"Could not get live channel data for {channel_id}")
            return 1

        # Ensure successful response and extract latest cut without strict model parsing
        try:
            message_code = data["messages"][0]["code"]
            if message_code != 100:
                message = data["messages"][0].get("message", "")
                typer.echo(f"SXM returned error {message_code} {message}")
                return 1
            live_channel_data = data["moduleList"]["modules"][0]["moduleResponse"][
                "liveChannelData"
            ]
        except (KeyError, IndexError):
            typer.echo("Error parsing SXM live channel response")
            return 1
        # Compute latest cut from markerLists
        marker_lists = live_channel_data.get("markerLists", [])
        cut_markers = []
        for marker_list in marker_lists:
            if marker_list.get("layer") == "cut":
                for m in marker_list.get("markers", []):
                    if "cut" in m:
                        cut_markers.append(m)

        if not cut_markers:
            typer.echo(f"Could not get latest cut for {channel_id}")
            return 1

        # Choose latest by time <= now (ms)
        import time as _time

        now_ms = int(_time.time() * 1000)
        cut_markers.sort(key=lambda x: x.get("time", 0))
        latest = None
        for m in cut_markers:
            if m.get("time", 0) <= now_ms:
                latest = m
            else:
                break

        if latest is None:
            latest = cut_markers[-1]

        cut = latest.get("cut", {})
        title = cut.get("title") or "Unknown"
        artists = cut.get("artists") or []
        artist = artists[0]["name"] if artists else "Unknown"
        album = None
        if "album" in cut and cut["album"]:
            album = cut["album"].get("title")

        typer.echo(f"Currently playing on {channel_id}:")
        typer.echo(f"  Title: {title}")
        typer.echo(f"  Artist: {artist}")
        if album:
            typer.echo(f"  Album: {album}")
    return 0


def main():
    app()
