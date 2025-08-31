"""HTTP Server module for sxm"""

import json
import logging
import time
from asyncio import get_event_loop, sleep
from time import monotonic
from typing import Any, Callable, Coroutine, Dict, List, Optional

from aiohttp import web

from sxm.client import HLS_AES_KEY, SegmentRetrievalException, SXMClient, SXMClientAsync

__all__ = ["make_http_handler", "run_http_server"]


def make_http_handler(
    sxm: SXMClientAsync, precache: bool = True
) -> Callable[[web.Request], Coroutine[Any, Any, web.Response]]:
    """
    Creates and returns a configured `aiohttp` request handler ready to be used
    by a :meth:`aiohttp.web.run_app` instance with your :class:`SXMClient`.

    Really useful if you want to create your own HTTP server as part
    of another application.

    Parameters
    ----------
    sxm : :class:`SXMClient`
        SXM client to use
    """

    aac_cache: Dict[str, bytes] = {}
    playlist_cache: Dict[str, str] = {}
    active_channel_id: Optional[str] = None

    def set_active(channel_id: Optional[str], initial_playlist: Optional[str] = None):
        active_channel_id = channel_id  # pylint: disable=unused-variable  # noqa

        if precache and channel_id is not None and initial_playlist is not None:
            loop = get_event_loop()
            loop.create_task(cache_playlist(channel_id, initial_playlist.split("\n")))

    async def get_segment(path: str):
        try:
            data = await sxm.get_segment(path)
        except SegmentRetrievalException:
            await sxm.close_session()
            sxm.reset_session()
            await sxm.authenticate()
            data = await sxm.get_segment(path)

        return data

    async def cache_playlist_chunks(end: float, playlist: List[str]):
        for item in playlist:
            if monotonic() >= end:
                return

            while len(aac_cache) > 10:
                await sleep(1)

            if not item.startswith("AAC_Data"):
                continue

            data = await get_segment(item)
            if data is not None:
                aac_cache[item] = data
            await sleep(1)

    async def cache_playlist(channel_id: str, playlist: List[str]):
        start = monotonic() - 3

        while active_channel_id == channel_id:
            await cache_playlist_chunks(start + 5, playlist)

            new_playlist: Optional[str] = None
            while new_playlist is None:
                new_playlist = await sxm.get_playlist(channel_id)

            playlist_cache[channel_id] = new_playlist
            playlist = new_playlist.split("\n")
            start = monotonic()

    async def get_playlist_chunk(segment_path: str):
        if segment_path in aac_cache:
            data = aac_cache[segment_path]
            del aac_cache[segment_path]
        else:
            data = await get_segment(segment_path)

        return data

    async def get_playlist(channel_id: str):
        if channel_id in playlist_cache:
            playlist: Optional[str] = playlist_cache[channel_id]
            del playlist_cache[channel_id]
        else:
            playlist = await sxm.get_playlist(channel_id)

        if active_channel_id != channel_id and playlist is not None:
            set_active(channel_id, playlist)

        return playlist

    async def sxm_handler(request: web.Request):
        """SXM Response handler"""

        response = web.Response(status=404)
        if request.path == "/now_playing":
            # Query param: channel=<id|name|number>
            channel_q = request.query.get("channel")
            if not channel_q:
                return web.Response(status=400)

            try:
                channel = await sxm.get_channel(channel_q)
            except Exception as e:  # noqa: BLE001
                logging.exception("Error resolving channel %s: %s", channel_q, e)
                channel = None

            if channel is None:
                return web.Response(status=404)

            try:
                data = await sxm.get_now_playing(channel)
            except Exception as e:  # noqa: BLE001
                logging.exception("Error fetching now playing for %s: %s", channel_q, e)
                data = None

            if data is None:
                return web.Response(status=503)

            # Validate response status and extract live channel data
            try:
                message_code = data["messages"][0]["code"]
                if message_code != 100:
                    return web.Response(status=503)
                live_channel_data = data["moduleList"]["modules"][0]["moduleResponse"][
                    "liveChannelData"
                ]
            except (KeyError, IndexError):
                return web.Response(status=500)

            marker_lists = live_channel_data.get("markerLists", [])
            cut_markers: List[Dict[str, Any]] = []  # type: ignore[name-defined]
            for marker_list in marker_lists:
                if marker_list.get("layer") == "cut":
                    for m in marker_list.get("markers", []):
                        if "cut" in m:
                            cut_markers.append(m)

            if not cut_markers:
                return web.Response(status=503)

            now_ms = int(time.time() * 1000)
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

            payload = {
                "channel_id": channel.id,
                "title": title,
                "artist": artist,
                "album": album,
                "played_at_ms": latest.get("time"),
            }

            return web.Response(
                status=200,
                body=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
        elif request.path.endswith(".m3u8"):
            channel_id = request.path.rsplit("/", 1)[1][:-5]
            try:
                playlist = await get_playlist(channel_id)
            except Exception as e:  # noqa: BLE001
                logging.exception("Error generating playlist for %s: %s", channel_id, e)
                playlist = None

            if playlist:
                response = web.Response(
                    status=200,
                    body=bytes(playlist, "utf-8"),
                    headers={"Content-Type": "application/x-mpegURL"},
                )
            else:
                set_active(None)
                response = web.Response(status=503)
        elif request.path.endswith(".aac"):
            segment_path = request.path[1:]
            data = await get_playlist_chunk(segment_path)

            if data:
                response = web.Response(
                    status=200,
                    body=data,
                    headers={"Content-Type": "audio/x-aac"},
                )
            else:
                response = web.Response(status=503)
        elif request.path.endswith("/key/1"):
            response = web.Response(
                status=200,
                body=HLS_AES_KEY,
                headers={"Content-Type": "text/plain"},
            )
        elif request.path.endswith("/channels/"):
            try:
                raw_channels = await sxm.get_channels()
            except Exception:
                raw_channels = []

            if len(raw_channels) > 0:
                response = web.Response(
                    status=200,
                    body=json.dumps(raw_channels).encode("utf-8"),
                    headers={"Content-Type": "application/json; charset=utf-8"},
                )
            else:
                response = web.Response(status=403)

        return response

    return sxm_handler


def run_http_server(
    sxm: SXMClient,
    port: int,
    ip="0.0.0.0",  # nosec
    logger: logging.Logger = None,
    precache: bool = True,
) -> None:
    """
    Creates and runs an instance of :class:`http.server.HTTPServer` to proxy
    SXM requests without authentication.

    You still need a valid SXM account with streaming rights,
    via the :class:`SXMClient`.

    Parameters
    ----------
    port : :class:`int`
        Port number to bind SXM Proxy server on
    ip : :class:`str`
        IP address to bind SXM Proxy server on
    """

    if logger is None:
        logger = logging.getLogger(__file__)

    if not sxm.authenticate():
        logging.fatal("Could not log into SXM")
        exit(1)

    if not sxm.configuration:
        logging.fatal("Could not get SXM configuration")
        exit(1)

    app = web.Application()
    app.router.add_get("/{_:.*}", make_http_handler(sxm.async_client))
    try:
        logger.info(f"running SXM proxy server on http://{ip}:{port}")
        web.run_app(
            app,
            host=ip,
            port=port,
            access_log=logger,
            print=None,  # type: ignore
        )
    except KeyboardInterrupt:
        pass
