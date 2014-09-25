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
from requests.auth import HTTPBasicAuth
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


class _AuthHeaderGrabberFakeRequest(object):
    def __init__(self):
        self.headers = {}

    @property
    def auth_header_value(self):
        return self.headers.get("Authorization")


def basic_auth_header_value(api_key):
    r = _AuthHeaderGrabberFakeRequest()
    HTTPBasicAuth(api_key, "x")(r)
    return r.auth_header_value


def strip_note_content(content):
    """
    Sometimes note content is returned wrapped in HTML.
    """
    content = content.strip()
    if content.startswith("<p>") and content.endswith("</p>"):
        content = content[3:-4]
    return content


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
        # We reset the Accept-Encoding header to avoid storing (opaque) gzip
        # response data.
        self.betamax_session.headers["Accept-Encoding"] = ""
        self.betamax = Betamax(
            self.betamax_session, cassette_library_dir=CASSETTE_LIBRARY_DIR)

        self.common_session = Session()
        # We reset the Accept-Encoding header to avoid storing (opaque) gzip
        # response data.
        self.common_session.headers["Accept-Encoding"] = ""
        self.betamax_common = Betamax(
            self.common_session, cassette_library_dir=CASSETTE_LIBRARY_DIR)

        self.betamax_placeholders = []
        self.common_snappy = self._get_common_snappy()

    def tearDown(self):
        self.betamax.stop()
        self.betamax_common.stop()

    def add_betamax_placeholder(self, placeholder, replace):
        placeholder_dict = {"placeholder": placeholder, "replace": replace}
        if placeholder_dict not in self.betamax_placeholders:
            self.betamax_placeholders.append(placeholder_dict)

    def snappy_for_session(self, session, api_key=None, api_url=None):
        """
        Build a ``SnappyApiSender`` instance using the provided session.
        """
        if api_key is None:
            api_key = self.api_key
        return SnappyApiSender(api_key, api_url=api_url, session=session)

    def _snappy_for_betamax(self, betamax, cassette_name, api_key, api_url):
        """
        Build a ``SnappyApiSender`` instance using the provided betamax object.
        """
        if api_key is None:
            api_key = self.api_key
        auth_header_value = basic_auth_header_value(api_key)
        self.add_betamax_placeholder("$AUTH_HEADER$", auth_header_value)
        betamax.use_cassette(
            cassette_name, record=self.betamax_record,
            serialize_with="prettyjson",
            placeholders=self.betamax_placeholders,
            match_requests_on=["method", "uri"])
        betamax.start()
        return self.snappy_for_session(betamax.session, api_key, api_url)

    def get_snappy(self, api_key=None, api_url=None):
        """
        Build a ``SnappyApiSender`` instance using the test session.
        """
        return self._snappy_for_betamax(
            self.betamax, self.id(), api_key, api_url)

    def _get_common_snappy(self, api_key=None, api_url=None):
        """
        Build a ``SnappyApiSender`` instance using the common session.

        This uses a shared betamax cassette and is suitable for requests that
        set up the environment for the test to use rather than being part of
        the test logic.
        """
        return self._snappy_for_betamax(
            self.betamax_common, "common", api_key, api_url)

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

    def get_staff_id(self):
        """
        Get a staff_id for use in further tests.

        This uses the common betamax instead of the test-specific one.

        Because we don't have very much control over the account we're testing
        against, we always choose the first staff entry in first account in the
        list.
        """
        account_id = self.get_account_id()
        staff = self.common_snappy.get_staff(account_id)
        return staff[0]["id"]

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

    def assert_looks_like_staff_dict(self, obj):
        """
        Assertion fails if the provided object doesn't look sufficiently like
        a staff dict.

        TODO: Determine if this is good enough.
        """
        self.assertTrue(isinstance(obj, dict), "Not a dict: %r" % (obj,))
        staff_fields = set([
            "id", "email", "sms_number", "first_name", "last_name", "photo",
            "culture", "notify", "created_at", "updated_at", "signature",
            "tour_played", "timezone", "notify_new", "news_read_at",
            "username"])
        missing_fields = staff_fields - set(obj.keys())
        self.assertEqual(
            missing_fields, set(), "Dict missing staff fields: %s" % (
                ", ".join(sorted(missing_fields)),))

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

    def test_get_staff(self):
        """
        ``.get_staff()`` returns a list of staffes for an account.

        Because we don't have very much control over the account we're testing
        against, we can only assert on the general structure. We always choose
        the first account in the list.
        """
        account_id = self.get_account_id()
        snappy = self.get_snappy()
        staff = snappy.get_staff(account_id)
        self.assertTrue(isinstance(staff, list))
        self.assertTrue(len(staff) >= 1)
        staff_member = staff[0]
        self.assert_looks_like_staff_dict(staff_member)
        # TODO: Make a call that requires a staff identifier and assert that
        #       it succeeds.

    def test_create_note_new_ticket(self):
        """
        Creating a note without a ticket identifier creates a new ticket.
        """
        # NOTE: This placeholder needs to be set before we create the API
        #       object betamax only loads its cassette data once upfront in
        #       playback mode.
        subject_uuid = str(uuid.uuid4())
        self.betamax_placeholders.append({
            "placeholder": "$SUBJECT_UUID$",
            "replace": subject_uuid,
        })

        mailbox_id = self.get_mailbox_id()
        snappy = self.get_snappy()

        ticket_subject = "Test subject %s" % (subject_uuid,)
        content = "What are the experiment protocols for subject %s?" % (
            subject_uuid,)
        ticket_id = snappy.create_note(
            mailbox_id, ticket_subject, content, from_addr=[{
                "name": "John Smith",
                "address": "john.smith@gmail.com",
            }])
        ticket_notes = snappy.get_ticket_notes(ticket_id)

        # A new ticket will only have one note.
        self.assertEqual(
            len(ticket_notes), 1, "Expected exactly 1 note, got %s: %r" % (
                len(ticket_notes), ticket_notes))
        [ticket_note] = ticket_notes

        # The note content should match the content we sent.
        self.assertEqual(strip_note_content(ticket_note["content"]), content)

    def test_create_note_new_private_from_staff(self):
        """
        Creating a note without a ticket identifier creates a new ticket.
        """
        # NOTE: This placeholder needs to be set before we create the API
        #       object betamax only loads its cassette data once upfront in
        #       playback mode.
        subject_uuid = str(uuid.uuid4())
        self.betamax_placeholders.append({
            "placeholder": "$SUBJECT_UUID$",
            "replace": subject_uuid,
        })

        mailbox_id = self.get_mailbox_id()
        staff_id = self.get_staff_id()
        snappy = self.get_snappy()

        ticket_subject = "Private subject %s" % (subject_uuid,)
        content = "Has %s accepted the privacy policy?" % (subject_uuid,)
        addr = {
            "name": "John Smith",
            "address": "john.smith@gmail.com",
        }
        ticket_id = snappy.create_note(
            mailbox_id, ticket_subject, content, to_addr=[addr],
            staff_id=staff_id, scope="private")
        ticket_notes = snappy.get_ticket_notes(ticket_id)

        # A new ticket will only have one note.
        self.assertEqual(
            len(ticket_notes), 1, "Expected exactly 1 note, got %s: %r" % (
                len(ticket_notes), ticket_notes))
        [ticket_note] = ticket_notes

        # The note content should match the content we sent.
        self.assertEqual(strip_note_content(ticket_note["content"]), content)

    def test_create_note_existing_ticket(self):
        """
        Creating a note with a ticket identifier adds a note to the ticket.
        """
        # NOTE: This placeholder needs to be set before we create the API
        #       object betamax only loads its cassette data once upfront in
        #       playback mode.
        subject_uuid = str(uuid.uuid4())
        self.betamax_placeholders.append({
            "placeholder": "$SUBJECT_UUID$",
            "replace": subject_uuid,
        })

        mailbox_id = self.get_mailbox_id()
        snappy = self.get_snappy()

        # Create ticket
        ticket_subject = "Test subject %s" % (subject_uuid,)
        content = "What are the experiment protocols for subject %s?" % (
            subject_uuid,)
        ticket_id = snappy.create_note(
            mailbox_id, ticket_subject, content, from_addr=[{
                "name": "John Smith",
                "address": "john.smith@gmail.com",
            }])

        # Add a note to existing ticket.
        content_2 = "Do we need more goop for %s?" % (subject_uuid,)
        ticket_id_2 = snappy.create_note(
            mailbox_id, ticket_subject, content_2, ticket_id=ticket_id,
            from_addr=[{
                "name": "John Smith",
                "address": "john.smith@gmail.com",
            }])

        # The ticket identifier should be the same.
        self.assertEqual(ticket_id, ticket_id_2)

        ticket_notes = snappy.get_ticket_notes(ticket_id)
        self.assertEqual(
            len(ticket_notes), 2, "Expected exactly 2 notes, got %s: %r" % (
                len(ticket_notes), ticket_notes))
        # NOTE: We have observed that the notes are ordered from newest to
        #       oldest, but this is not documented. The note identifier appears
        #       to be an increasing integer, but this is also not documented.
        #       The timestamp lacks sufficient resolution to order the notes.
        #       For now, we assume the observed ordering is consistent.
        [note_2, note_1] = ticket_notes

        # The note content should match the content we sent.
        self.assertEqual(strip_note_content(note_1["content"]), content)
        self.assertEqual(strip_note_content(note_2["content"]), content_2)
