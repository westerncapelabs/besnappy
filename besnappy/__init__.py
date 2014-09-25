"""An unofficial client library for the BeSnappy HTTP API.."""

__version__ = "0.0.1a"

from .tickets import SnappyApiSender

__all__ = [
    'SnappyApiSender',
]
