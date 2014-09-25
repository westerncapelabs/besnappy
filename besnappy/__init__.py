"""An unofficial client library for the BeSnappy HTTP API.."""

__version__ = "0.1.0a"

from .tickets import SnappyApiSender

__all__ = [
    'SnappyApiSender',
]
