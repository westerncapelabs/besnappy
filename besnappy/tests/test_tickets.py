"""
Tests for besnappy.tickets.
"""

from unittest import TestCase

from requests import HTTPError
from requests.adapters import HTTPAdapter
from requests_testadapter import TestSession, Resp, TestAdapter

from fake_besnappy import Request, FakeSnappyApiSender

from besnappy.tickets import SnappyApiSender


