# -*- coding: utf-8 -*-

"""Top-level package for sxm."""

from sxm.client import (
    HLS_AES_KEY,
    AuthenticationError,
    SegmentRetrievalException,
    SXMClient,
    SXMClientAsync,
)
from sxm.http import make_http_handler, run_http_server
from sxm.models import QualitySize, RegionChoice

__author__ = """AngellusMortis"""
__email__ = "cbailey@mort.is"
__version__ = "0.2.8"
__all__ = [
    "AuthenticationError",
    "HLS_AES_KEY",
    "make_http_handler",
    "run_http_server",
    "SegmentRetrievalException",
    "SXMClient",
    "SXMClientAsync",
    "RegionChoice",
    "QualitySize",
]
