"""STOMP client for Network Rail's public data."""

__version__ = '0.0.1'

from .client import NetworkRailClient
from .manager import process, run_demo
from .store import DummyFrameStore
