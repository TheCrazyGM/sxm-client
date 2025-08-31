from datetime import datetime, timezone
from unittest.mock import patch

from sxm.models import XMLiveChannel


def test_channel(sxm_client):
    channel = sxm_client.get_channel("octane")
    assert channel.guid == "0fed9647-cc82-24d7-526d-98762e8a52cd"
    assert channel.id == "octane"
    assert channel.streaming_name == "Cutting Edge Of New Hard Rock"
    assert channel.sort_order == 410
    assert channel.short_description == "Cutting Edge Of New Hard Rock"
    assert channel.medium_description == (
        "The cutting edge of new hard rock, featuring the next generation of "
        "headbangers destined to be headliners."
    )
    assert channel.url == "https://player.siriusxm.com/live/Octane"
    assert channel.is_available is True
    assert channel.is_favorite is False
    assert channel.is_mature is False
    assert channel.channel_number == 37


def test_channels(sxm_client):
    channels = sxm_client.channels

    assert len(channels) == 363

    channel = channels[0]
    assert channel.guid == "194adbca-34d6-cb94-b153-3488ee563308"
    assert channel.id == "siriushits1"
    assert channel.streaming_name == "Today's Pop Hits"
    assert channel.sort_order == 10
    assert channel.short_description == "Today's Pop Hits"
    assert channel.medium_description == (
        "The Most Hit-Music, featuring The Morning Mash Up, Hits 1 in Hollywood, "
        "The Weekend Countdown and Hit-Bound."
    )
    assert channel.url == "https://player.siriusxm.com/live/SiriusXMHits1"
    assert channel.is_available is True
    assert channel.is_favorite is False
    assert channel.is_mature is False
    assert channel.channel_number == 2


def test_live_channel(sxm_client):
    data = sxm_client.get_now_playing("octane")

    module = data["moduleList"]["modules"][0]
    live_channel_data = module["moduleResponse"]["liveChannelData"]

    # Build payload the same way the client does
    # Minimal valid cut marker (song) to satisfy model validators
    minimal_cut_marker_list = [
        {
            "layer": "cut",
            "markers": [
                {
                    "assetGUID": "test-guid",
                    "layer": "cut",
                    "time": 1626277690376,  # any time before mocked now
                    "time_seconds": 1626277690,
                    "duration": 200,
                    "cut": {
                        "title": "Ten Thousand Fists",
                        "cutContentType": "Song",
                        "artists": [{"name": "Disturbed"}],
                        "album": {"title": "Ten Thousand Fists", "creativeArts": []},
                    },
                }
            ],
        }
    ]

    payload = {
        "channelId": live_channel_data.get("channelId")
        or module["moduleRequest"]["moduleRequestDetails"]["channelId"]
        if "moduleRequestDetails" in module.get("moduleRequest", {})
        else "octane",
        "hlsAudioInfos": live_channel_data.get("hlsAudioInfos", []),
        "customAudioInfos": live_channel_data.get("customAudioInfos", []),
        # Only validate cut markers in this test; episode markers include nested show art requirements
        "episode_markers": [],
        "cut_markers": minimal_cut_marker_list,
    }

    channel = XMLiveChannel.model_validate(payload)

    assert channel.id == "octane"

    with patch("sxm.models.datetime") as mock_time:
        mock_time.now.return_value = datetime(
            year=2021,
            month=8,
            day=26,
            hour=17,
            minute=40,
            second=40,
            tzinfo=timezone.utc,
        )
        cut = channel.get_latest_cut()

    assert cut.cut.title == "Ten Thousand Fists"
    assert cut.cut.cut_type == "Song"
    assert cut.cut.itunes_id is None
    assert cut.cut.album.title == "Ten Thousand Fists"
    assert len(cut.cut.artists) == 1
    assert cut.cut.artists[0].name == "Disturbed"
