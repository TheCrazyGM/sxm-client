from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional, Union

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    validator,
)

__all__ = [
    "XMArt",
    "XMImage",
    "XMCategory",
    "XMMarker",
    "XMShow",
    "XMEpisode",
    "XMEpisodeMarker",
    "XMArtist",
    "XMAlbum",
    "XMCut",
    "XMSong",
    "XMCutMarker",
    "XMPosition",
    "XMHLSInfo",
    "XMChannel",
    "XMLiveChannel",
    "QualitySize",
    "RegionChoice",
]


LIVE_PRIMARY_HLS = "https://siriusxm-priprodlive.akamaized.net"
LIVE_SECONDARY_HLS = "https://siriusxm-secprodlive.akamaized.net"


def parse_xm_datetime(dt_string: str):
    dt_string = dt_string.replace("+0000", "")
    dt = datetime.fromisoformat(dt_string)
    return dt.replace(tzinfo=timezone.utc)


def parse_xm_timestamp(timestamp: int):
    return datetime.utcfromtimestamp(timestamp / 1000).replace(tzinfo=timezone.utc)


class QualitySize(str, Enum):
    SMALL_64k = "SMALL"
    MEDIUM_128k = "MEDIUM"
    LARGE_256k = "LARGE"


class RegionChoice(str, Enum):
    US = "US"
    CA = "CA"


class SXMBaseModel(BaseModel):
    class Config:
        allow_population_by_field_name = True


class XMArt(SXMBaseModel):
    name: Optional[str]
    url: str
    art_type: str = Field(..., alias="type")


class XMImage(XMArt):
    platform: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    size: Optional[str] = None
    art_type: str = "IMAGE"


class XMCategory(SXMBaseModel):
    guid: str = Field(..., alias="categoryGuid")
    name: str
    key: Optional[str] = None
    order: Optional[int] = None
    short_name: Optional[str] = Field(None, alias="shortName")


class XMMarker(SXMBaseModel):
    guid: str = Field(..., alias="assetGUID")
    time: datetime
    time_seconds: int
    duration: timedelta

    @validator("time", pre=True)  # pylint: disable=no-self-argument
    def _validate_time(cls, v):
        return parse_xm_timestamp(v)

    @validator("time_seconds", pre=True, always=True)  # pylint: disable=no-self-argument
    def _validate_time_seconds(cls, v, values):
        return int(values["time"].timestamp())

    @validator("duration", pre=True)  # pylint: disable=no-self-argument
    def _validate_duration(cls, v):
        return timedelta(seconds=v)


class XMShow(SXMBaseModel):
    guid: str = Field(..., alias="showGUID")
    medium_title: str = Field(..., alias="mediumTitle")
    long_title: str = Field(..., alias="longTitle")
    short_description: str = Field(..., alias="shortDescription")
    long_description: str = Field(..., alias="longDescription")
    arts: List[XMArt] = Field(..., alias="creativeArts")

    @validator("arts", pre=True)  # pylint: disable=no-self-argument
    def _validate_arts(cls, v):
        return [art for art in v if art["type"] == "IMAGE"]


class XMEpisode(SXMBaseModel):
    guid: str = Field(..., alias="episodeGUID")
    medium_title: str = Field(..., alias="mediumTitle")
    long_title: str = Field(..., alias="longTitle")
    short_description: str = Field(..., alias="shortDescription")
    long_description: str = Field(..., alias="longDescription")
    show: XMShow


class XMEpisodeMarker(XMMarker, SXMBaseModel):
    episode: XMEpisode


class XMArtist(SXMBaseModel):
    name: str


class XMAlbum(SXMBaseModel):
    title: Optional[str] = None
    arts: List[XMArt] = Field([], alias="creativeArts")

    @validator("arts", pre=True)  # pylint: disable=no-self-argument
    def _validate_arts(cls, v):
        return [art for art in v if art["type"] == "IMAGE"]


class XMCut(SXMBaseModel):
    title: str
    artists: List[XMArtist]
    cut_type: Optional[str] = Field(None, alias="cutContentType")


class XMSong(XMCut, SXMBaseModel):
    album: Optional[XMAlbum] = None
    itunes_id: Optional[str] = Field(None, alias="externalIds")

    @validator("itunes_id", pre=True)  # pylint: disable=no-self-argument
    def _validate_itunes_id(cls, v):
        if v is None:
            return None

        for external_id in v:
            if external_id["id"] == "iTunes":
                return external_id["value"]
        return None


class XMCutMarker(XMMarker, SXMBaseModel):
    cut: Union[XMSong, XMCut]

    @validator("cut", pre=True)  # pylint: disable=no-self-argument
    def _validate_cut(cls, v):
        if v.get("cutContentType") == "Song":
            return XMSong.parse_obj(v)
        return XMCut.parse_obj(v)


class XMPosition(SXMBaseModel):
    timestamp: datetime
    position: str

    @validator("timestamp", pre=True)  # pylint: disable=no-self-argument
    def _validate_timestamp(cls, v):
        return parse_xm_datetime(v)


class XMHLSInfo(SXMBaseModel):
    name: str
    size: str
    position: Optional[XMPosition] = None
    url: str = Field(..., alias="url")

    _primary_root: str = PrivateAttr(LIVE_PRIMARY_HLS)
    _secondary_root: str = PrivateAttr(LIVE_SECONDARY_HLS)
    # + unused chunks

    _url_cache: Optional[str] = PrivateAttr(None)

    @property
    def resolved_url(self):
        if self._url_cache is None:
            if self.name == "primary":
                self._url_cache = self._primary_root + self.url
            else:
                self._url_cache = self._secondary_root + self.url
        return self._url_cache

    def set_hls_roots(self, primary: str, secondary: str):
        self._primary_root = primary
        self._secondary_root = secondary
        self._url_cache = None


class XMChannel(SXMBaseModel):
    """See `tests/sample_data/xm_channel.json` for sample"""

    guid: str = Field(..., alias="channelGuid")
    id: str = Field(..., alias="channelId")  # noqa A003
    name: str
    streaming_name: str = Field(..., alias="streamingName")
    sort_order: int = Field(..., alias="sortOrder")
    short_description: str = Field(..., alias="shortDescription")
    medium_description: str = Field(..., alias="mediumDescription")
    url: str
    is_available: bool = Field(..., alias="isAvailable")
    is_favorite: bool = Field(..., alias="isFavorite")
    is_mature: bool = Field(..., alias="isMature")
    channel_number: int = Field(..., alias="siriusChannelNumber")
    images: List[XMImage]
    categories: List[XMCategory]

    @validator("images", pre=True)  # pylint: disable=no-self-argument
    def _validate_images(cls, v):
        return v["images"]

    @validator("categories", pre=True)  # pylint: disable=no-self-argument
    def _validate_categories(cls, v):
        return v["categories"]

    @property
    def pretty_name(self) -> str:
        """Returns a formated version of channel number + channel name"""
        return f"#{self.channel_number} {self.name}"


class XMLiveChannel(SXMBaseModel):
    """See `tests/sample_data/xm_live_channel.json` for sample"""

    id: str = Field(..., alias="channelId")  # noqa A003
    hls_infos: List[XMHLSInfo] = Field(..., alias="hlsAudioInfos")
    custom_hls_infos: List[XMHLSInfo] = Field(..., alias="customAudioInfos")
    episode_markers: List[XMEpisodeMarker]
    cut_markers: List[XMCutMarker]
    tune_time: Optional[datetime] = None

    _stream_quality: QualitySize = PrivateAttr(QualitySize.LARGE_256k)
    _song_cuts: Optional[List[XMCutMarker]] = PrivateAttr(None)
    _primary_hls: Optional[XMHLSInfo] = PrivateAttr(None)
    _secondary_hls: Optional[XMHLSInfo] = PrivateAttr(None)

    @validator("tune_time", pre=True)  # pylint: disable=no-self-argument
    def _validate_tune_time(cls, v, values):
        return parse_xm_datetime(v)

    @validator("episode_markers", pre=True)  # pylint: disable=no-self-argument
    def _validate_episode_markers(cls, v):
        markers = []
        for marker_list in v:
            if marker_list["layer"] == "episode":
                for marker in marker_list["markers"]: # pylint: disable=not-an-iterable
                    markers.append(XMEpisodeMarker.parse_obj(marker))
        return sorted(markers, key=lambda x: x.time)

    @validator("cut_markers", pre=True)  # pylint: disable=no-self-argument
    def _validate_cut_markers(cls, v):
        markers = []
        for marker_list in v:
            if marker_list["layer"] == "cut":
                for marker in marker_list["markers"]: # pylint: disable=not-an-iterable
                    if "cut" in marker:
                        markers.append(XMCutMarker.parse_obj(marker))
        return sorted(markers, key=lambda x: x.time)

    def set_stream_quality(self, value: QualitySize):
        self._stream_quality = value
        self._primary_hls = None
        self._secondary_hls = None

    def set_hls_roots(self, primary: str, secondary: str):
        for hls_info in self.hls_infos: # pylint: disable=not-an-iterable
            hls_info.set_hls_roots(primary, secondary)

        for hls_info in self.custom_hls_infos: # pylint: disable=not-an-iterable
            hls_info.set_hls_roots(primary, secondary)

    @property
    def primary_hls(self) -> XMHLSInfo:
        if self._primary_hls is None:
            for hls_info in self.hls_infos: # pylint: disable=not-an-iterable
                if hls_info.name == "primary":
                    self._primary_hls = hls_info
                    # found the one we really want
                    if hls_info.size == self._stream_quality.value:
                        break

        return self._primary_hls  # type: ignore

    @property
    def secondary_hls(self) -> XMHLSInfo:
        if self._secondary_hls is None:
            for hls_info in self.hls_infos: # pylint: disable=not-an-iterable
                if hls_info.name == "secondary":
                    self._secondary_hls = hls_info
                    # found the one we really want
                    if hls_info.size == self._stream_quality:
                        break

        return self._secondary_hls  # type: ignore

    @property
    def song_cuts(self) -> List[XMCutMarker]:
        """Returns a list of all `XMCut` objects that are for songs"""

        if self._song_cuts is None:
            self._song_cuts = []
            for cut in self.cut_markers:
                if isinstance(cut.cut, XMSong):
                    self._song_cuts.append(cut)

        return self._song_cuts

    @staticmethod
    def sort_markers(markers: List[XMMarker]) -> List[XMMarker]:
        """Sorts a list of `XMMarker` objects"""
        return sorted(markers, key=lambda x: x.time)

    def _latest_marker(
        self, marker_attr: str, now: Optional[datetime] = None
    ) -> Union[XMMarker, None]:
        """Returns the latest `XMMarker` based on type relative to now"""

        markers: Optional[List[XMMarker]] = getattr(self, marker_attr)
        if markers is None:
            return None

        if now is None:
            now = datetime.now(timezone.utc)

        now_sec = int(now.timestamp())
        latest = None
        for marker in markers:
            if now_sec <= marker.time_seconds:
                break
            latest = marker
        return latest

    def get_latest_episode(
        self, now: Optional[datetime] = None
    ) -> Union[XMEpisodeMarker, None]:
        """Returns the latest :class:`XMEpisodeMarker` based
        on type relative to now

        Parameters
        ----------
        now : Optional[:class:`datetime`]
        """
        return self._latest_marker("episode_markers", now)  # type: ignore

    def get_latest_cut(
        self, now: Optional[datetime] = None
    ) -> Union[XMCutMarker, None]:
        """Returns the latest :class:`XMCutMarker` based
        on type relative to now

        Parameters
        ----------
        now : Optional[:class:`datetime`]
        """
        return self._latest_marker("cut_markers", now)  # type: ignore


    def get_latest_song(
        self, now: Optional[datetime] = None
    ) -> Union[XMCutMarker, None]:
        """Returns the latest :class:`XMCutMarker` that is a song based
        on type relative to now

        Parameters
        ----------
        now : Optional[:class:`datetime`]
        """
        return self._latest_marker("song_cuts", now)  # type: ignore
