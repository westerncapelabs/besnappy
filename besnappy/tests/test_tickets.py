"""
Tests for besnappy.tickets.
"""

import json
import os
from unittest import TestCase
import uuid

from betamax import Betamax
from betamax.serializers import JSONSerializer
from requests import Session
from requests_testadapter import TestSession, TestAdapter

from besnappy.tickets import SnappyApiSender


CASSETTE_LIBRARY_DIR = os.path.join(os.path.dirname(__file__), "cassettes")
BESNAPPY_TEST_API_KEY = os.environ.get("BESNAPPY_TEST_API_KEY")


class PrettyJSONSerializer(JSONSerializer):
    name = 'prettyjson'

    def serialize(self, cassette_data):
        return json.dumps(
            cassette_data, sort_keys=True, indent=2, separators=(',', ': '))


Betamax.register_serializer(PrettyJSONSerializer)


class TestSnappyApiSender(TestCase):
    def setUp(self):
        self.api_key = "dummy_key"
        self.betamax_record = "none"
        if os.environ.get("BESNAPPY_TEST_RECORD_REQUESTS"):
            if BESNAPPY_TEST_API_KEY:
                self.betamax_record = "all"
                self.api_key = BESNAPPY_TEST_API_KEY
            else:
                raise RuntimeError(
                    "BESNAPPY_TEST_RECORD_REQUESTS is set, but"
                    " BESNAPPY_TEST_API_KEY is not.")

        self.no_http_session = TestSession()
        self.betamax_session = Session()
        self.betamax = Betamax(
            self.betamax_session, cassette_library_dir=CASSETTE_LIBRARY_DIR)
        self.common_session = Session()
        self.betamax_common = Betamax(
            self.common_session, cassette_library_dir=CASSETTE_LIBRARY_DIR)

    def tearDown(self):
        self.betamax.stop()
        self.betamax_common.stop()

    def snappy_for_session(self, session, api_key=None, api_url=None):
        """
        Build a ``SnappyApiSender`` instance using the provided session.
        """
        if api_key is None:
            api_key = self.api_key
        return SnappyApiSender(api_key, api_url=api_url, session=session)

    def get_snappy(self, api_key=None, api_url=None):
        """
        Build a ``SnappyApiSender`` instance using the test session.
        """
        self.betamax.use_cassette(
            self.id(), record=self.betamax_record, serialize_with="prettyjson")
        self.betamax.start()
        return self.snappy_for_session(self.betamax_session, api_key, api_url)

    def get_common_snappy(self, api_key=None, api_url=None):
        """
        Build a ``SnappyApiSender`` instance using the common session.

        This uses a shared betamax cassette and is suitable for requests that
        set up the environment for the test to use rather than being part of
        the test logic.
        """
        self.betamax_common.use_cassette(
            "common", record=self.betamax_record, serialize_with="prettyjson")
        self.betamax_common.start()
        return self.snappy_for_session(self.common_session, api_key, api_url)

    def test_api_request_url_construction_default_api_url(self):
        """
        ``._api_request()`` constructs a URL by appending the ``endpoint`` to
        the ``api_url``. In this case, we use the default API URL.
        """
        snappy = self.snappy_for_session(self.no_http_session)
        self.no_http_session.mount(
            "%s/flash" % (snappy.api_url,), TestAdapter("ok"))

        resp = snappy._api_request("GET", "flash")
        self.assertEqual(resp.content, "ok")

    def test_api_request_url_construction_custom_api_url(self):
        """
        ``._api_request()`` constructs a URL by appending the ``endpoint`` to
        the ``api_url``. In this case, we provide a custom API URL.
        """
        snappy = self.snappy_for_session(
            self.no_http_session, api_url="http://snappyapi.example.com/v1")
        self.no_http_session.mount(
            "http://snappyapi.example.com/v1/flash", TestAdapter("ok"))

        resp = snappy._api_request("GET", "flash")
        self.assertEqual(resp.content, "ok")

    def test_note_foo(self):
        """
        XXX: This is a temporary test method to prototype the use of betamax.
        """
        common_snappy = self.get_common_snappy()
        resp = common_snappy.get_accounts()
        account_id = resp[0]["id"]
        resp = common_snappy.get_mailboxes(account_id)
        mailbox_id = resp[0]["id"]
        snappy = self.get_snappy()
        resp = snappy.note(
            mailbox_id, "Test subject %s" % (uuid.uuid4(),),
            "Are all experiment protocols being followed?", from_addr=[{
                "name": "John Smith",
                "address": "john.smith@gmail.com",
            }])
