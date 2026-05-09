"""SloppyTron body provider package."""

from sloppy_tron.provider.contract import AFFORDANCES, PROVIDER_ID
from sloppy_tron.provider.fake_backend import FakeBodyBackend
from sloppy_tron.provider.reachy_backend import ReachyDaemonBackend
from sloppy_tron.provider.slop_server import create_slop_server

__all__ = [
    "AFFORDANCES",
    "PROVIDER_ID",
    "FakeBodyBackend",
    "ReachyDaemonBackend",
    "create_slop_server",
]
