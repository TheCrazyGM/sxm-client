import json
import pathlib
from unittest.mock import MagicMock

import pytest

from sxm import SXMClient

BASE_DIR = pathlib.Path(__file__).parent.absolute()
SAMPLE_DIR = BASE_DIR / "tests" / "sample_data"


@pytest.fixture
def xm_channels_response():
    with open(SAMPLE_DIR / "xm_channels.json", "r") as json_file:
        xm_channels_response = json.load(json_file)

    return xm_channels_response["moduleList"]["modules"][0]["moduleResponse"][
        "contentData"
    ]["channelListing"]["channels"]


@pytest.fixture
def xm_live_channel_response():
    with open(SAMPLE_DIR / "xm_live_channel.json", "r") as json_file:
        xm_live_channel_response = json.load(json_file)

    return xm_live_channel_response


@pytest.fixture
def sxm_client(xm_channels_response, xm_live_channel_response):
    sxm = SXMClient("user", "password", region="US")
    get_channels = MagicMock(return_value=xm_channels_response)

    sxm.get_channels = get_channels
    sxm.get_now_playing = MagicMock(return_value=xm_live_channel_response)

    # Provide an async version for the async client (Python 3.13: asyncio.coroutine is removed)
    async def _get_channels_async():
        return xm_channels_response

    sxm.async_client.get_channels = _get_channels_async  # type: ignore[attr-defined]

    return sxm
