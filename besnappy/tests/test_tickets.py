"""
Tests for besnappy.tickets.
"""

from unittest import TestCase

from requests_testadapter import TestSession, TestAdapter

from besnappy.tickets import SnappyApiSender


class TestSnappyApiSender(TestCase):
    def setUp(self):
        self.session = TestSession()

    def get_snappy(self, api_key="dummy_key", api_url=None):
        """
        Build a ``SnappyApiSender`` instance using the test session.
        """
        return SnappyApiSender(api_key, api_url=api_url, session=self.session)

    def test_api_request_url_construction_default_api_url(self):
        """
        ``._api_request()`` constructs a URL by appending the ``endpoint`` to
        the ``api_url``. In this case, we use the default API URL.
        """
        snappy = self.get_snappy()
        self.session.mount("%s/flash" % (snappy.api_url,), TestAdapter("ok"))

        resp = snappy._api_request("GET", "flash")
        self.assertEqual(resp.content, "ok")

    def test_api_request_url_construction_custom_api_url(self):
        """
        ``._api_request()`` constructs a URL by appending the ``endpoint`` to
        the ``api_url``. In this case, we provide a custom API URL.
        """
        snappy = self.get_snappy(api_url="http://snappyapi.example.com/v1")
        self.session.mount(
            "http://snappyapi.example.com/v1/flash", TestAdapter("ok"))

        resp = snappy._api_request("GET", "flash")
        self.assertEqual(resp.content, "ok")
