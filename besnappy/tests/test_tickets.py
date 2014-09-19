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
        self.common_snappy = self._get_common_snappy()

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

    def _get_common_snappy(self, api_key=None, api_url=None):
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

    ####################################
    # Tests for public API below here. #
    ####################################

    def get_account_id(self):
        """
        Get an account_id for use in further tests.

        This uses the common betamax instead of the test-specific one.

        Because we don't have very much control over the account we're testing
        against, we always choose the first account in the list.
        """
        accounts = self.common_snappy.get_accounts()
        return accounts[0]["id"]

    def get_mailbox_id(self):
        """
        Get a mailbox_id for use in further tests.

        This uses the common betamax instead of the test-specific one.

        Because we don't have very much control over the account we're testing
        against, we always choose the first mailbox in first account in the
        list.
        """
        account_id = self.get_account_id()
        mailboxes = self.common_snappy.get_mailboxes(account_id)
        return mailboxes[0]["id"]

    def assert_looks_like_account_dict(self, obj):
        """
        Assertion fails if the provided object doesn't look sufficiently like
        an account dict.

        TODO: Determine if this is good enough.
        """
        self.assertTrue(isinstance(obj, dict), "Not a dict: %r" % (obj,))
        account_fields = set([
            "id", "organization", "domain", "plan_id", "active", "created_at",
            "updated_at", "custom_domain"])
        missing_fields = account_fields - set(obj.keys())
        self.assertEqual(
            missing_fields, set(), "Dict missing account fields: %s" % (
                ", ".join(sorted(missing_fields)),))

    def assert_looks_like_mailbox_dict(self, obj, account_id):
        """
        Assertion fails if the provided object doesn't look sufficiently like
        a mailbox dict belonging to the specified account.

        TODO: Determine if this is good enough.
        """
        self.assertTrue(isinstance(obj, dict), "Not a dict: %r" % (obj,))
        mailbox_fields = set([
            "id", "account_id", "type", "address", "display",
            "auto_responding", "auto_response", "active", "created_at",
            "updated_at", "custom_address", "theme", "local_part"])
        missing_fields = mailbox_fields - set(obj.keys())
        self.assertEqual(
            missing_fields, set(), "Dict missing mailbox fields: %s" % (
                ", ".join(sorted(missing_fields)),))
        self.assertEqual(obj["account_id"], account_id)

    def test_get_accounts(self):
        """
        ``.get_accounts()`` returns a list of accounts.

        Because we don't have very much control over the account we're testing
        against, we can only assert on the general structure. We always choose
        the first account in the list.
        """
        snappy = self.get_snappy()
        accounts = snappy.get_accounts()
        self.assertTrue(isinstance(accounts, list))
        self.assertTrue(len(accounts) >= 1)
        account = accounts[0]
        self.assert_looks_like_account_dict(account)
        # TODO: Make a call that requires an account identifier and assert that
        #       it succeeds.

    def test_get_mailboxes(self):
        """
        ``.get_mailboxes()`` returns a list of mailboxes for an account.

        Because we don't have very much control over the account we're testing
        against, we can only assert on the general structure. We always choose
        the first account in the list.
        """
        account_id = self.get_account_id()
        snappy = self.get_snappy()
        mailboxes = snappy.get_mailboxes(account_id)
        self.assertTrue(isinstance(mailboxes, list))
        self.assertTrue(len(mailboxes) >= 1)
        mailbox = mailboxes[0]
        self.assert_looks_like_mailbox_dict(mailbox, account_id)
        # TODO: Make a call that requires a mailbox identifier and assert that
        #       it succeeds.

    def test_note_foo(self):
        """
        XXX: This is a temporary test method to prototype the use of betamax.
        """
        mailbox_id = self.get_mailbox_id()
        snappy = self.get_snappy()
        resp = snappy.note(
            mailbox_id, "Test subject %s" % (uuid.uuid4(),),
            "Are all experiment protocols being followed?", from_addr=[{
                "name": "John Smith",
                "address": "john.smith@gmail.com",
            }])
