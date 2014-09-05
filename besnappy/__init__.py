"""An unofficial client library for the BeSnappy HTTP API.."""

__version__ = "0.0.1a"

from .ticket import SnappyApiSender, LoggingSender

__all__ = [
    'SnappyApiSender', 'LoggingSender',
]
